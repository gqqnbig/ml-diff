using System;
using System.IO;
using System.Diagnostics;
using System.Reflection;
using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using System.Linq;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;

namespace DiffSyntax
{
	class Program
	{
		private static readonly ILogger logger;

		static Program()
		{
			string configFilePath = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(System.AppContext.BaseDirectory), "appsettings.json");
			if (System.IO.File.Exists(configFilePath) == false)
				Console.Error.WriteLine($"{configFilePath} doesn't exist.");
			var builder = new ConfigurationBuilder()
				.SetBasePath(Directory.GetCurrentDirectory())
				.AddJsonFile(configFilePath, optional: true, reloadOnChange: true);
			var configuration = builder.Build();
			ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
			{
				builder.AddConfiguration(configuration.GetSection("Logging")).AddConsole();
			});

			logger = loggerFactory.CreateLogger<Program>();
		}



		static void Main(string[] args)
		{
			//CheckIdentifierChanges(@"D:\renaming\data\generated\dataset\AntennaPod\no\007f92c291c280f7f58f17b8a849bdbd0d771608.diff");


			foreach (string path in System.IO.Directory.EnumerateFiles(@"D:\renaming\data\generated\dataset", "*.diff", SearchOption.AllDirectories))
			{
				string label = Path.GetFileName(Path.GetDirectoryName(path));
				Trace.Assert(label.Equals("yes", StringComparison.OrdinalIgnoreCase) || label.Equals("no", StringComparison.OrdinalIgnoreCase));

				try
				{
					if (CheckIdentifierChanges(path) == label.Equals("yes", StringComparison.OrdinalIgnoreCase))
					{
						Console.WriteLine($"{path} is good");
					}
					else
					{
						Console.WriteLine($"The label of {path} is {label}, but syntax analysis doesn't agree");
					}
				}
				catch (Exception e)
				{
					logger.LogError(new EventId(0), e, $"{path} caused error:\n{e.Message}", new object[0]);
					throw;
				}
			}
		}


		static bool CheckIdentifierChanges(string diffPath)
		{
			List<string> lines = new List<string>();
			using (StreamReader sr = new StreamReader(diffPath))
			{
				while (sr.EndOfStream == false)
					lines.Add(sr.ReadLine());
			}

			var uniqueInBefore = new List<IdentifierDeclarationInDiff>();
			var uniqueInAfter = new List<IdentifierDeclarationInDiff>();

			List<List<string>> snippets = new List<List<string>>(SplitDiffIntoSnippets(lines));


			for (int snippetIndex = 0; snippetIndex < snippets.Count; snippetIndex++)
			{
				var t = RecoverBeforeAfter(snippets[snippetIndex]);
				string before = t.Item1;
				string after = t.Item2;


				var beforeIdentifiers = FindDeclaredIdentifiersFromSnippet(before);
				var afterIdentifiers = FindDeclaredIdentifiersFromSnippet(after);


				var ub = new List<IdentifierDeclaration>(beforeIdentifiers);
				afterIdentifiers.ForEach(l => ub.Remove(l));
				uniqueInBefore.AddRange(from d in ub
										select new IdentifierDeclarationInDiff { IdentifierDeclaration = d, SnippetIndex = snippetIndex });

				var ua = new List<IdentifierDeclaration>(afterIdentifiers);
				beforeIdentifiers.ForEach(l => ua.Remove(l));

				uniqueInAfter.AddRange(from d in ua
									   select new IdentifierDeclarationInDiff { IdentifierDeclaration = d, SnippetIndex = snippetIndex });

				//logger.LogInformation("Found the following declared identifers: {0}.", string.Join(", ", from id in identifierCollector.DeclaredIdentifiers
				//																						 select id.Name + " from " + parser.RuleNames[id.Rule]));

			}

			if (uniqueInBefore.Count == 1 && uniqueInAfter.Count == 1)
			{
				Console.WriteLine($"This diff only changes one identifier, from {uniqueInBefore[0].IdentifierDeclaration.Name} to {uniqueInAfter[0].IdentifierDeclaration.Name}.");
				return true;
			}
			else if (uniqueInBefore.Count == 0 && uniqueInAfter.Count == 0)
			{
				Console.WriteLine("No identifier changes.");
				return false;
			}
			else
			{
				string b = string.Join(", ", from i in uniqueInBefore
											 select i.IdentifierDeclaration.Name);
				string a = string.Join(", ", from i in uniqueInAfter
											 select i.IdentifierDeclaration.Name);

				Console.WriteLine($"There are multiple identifier changes in this diff.\nBefore: {b}\nAfter: {a}.");
				return false;
			}
		}

		static int PopulateTokens(ITokenStream tokens)
		{
			while (tokens.LA(1) != IntStreamConstants.EOF)
				tokens.Consume();

			Debug.Assert(tokens.Index == tokens.Size - 1);
			return tokens.Size;

		}

		private static Tuple<string, string> RecoverBeforeAfter(List<string> lines)
		{
			List<string> beforeLines = new List<string>();
			List<string> afterLines = new List<string>();

			for (int i = 0; i < lines.Count; i++)
			{
				if (lines[i].StartsWith("-"))
					beforeLines.Add(lines[i].Substring(1));
				else if (lines[i].StartsWith("+"))
					afterLines.Add(lines[i].Substring(1));
				else
				{
					beforeLines.Add(lines[i].Substring(1));
					afterLines.Add(lines[i].Substring(1));
				}
			}
			return Tuple.Create(string.Join("\n", beforeLines), string.Join("\n", afterLines));
		}


		private static IEnumerable<List<string>> SplitDiffIntoSnippets(List<string> diffLines)
		{
			int snipetStart = -1;
			for (int i = 0; i < diffLines.Count; i++)
			{
				if (diffLines[i].StartsWith("@@"))
				{
					if (snipetStart != -1)
					{
						yield return diffLines.GetRange(snipetStart, i - snipetStart);
					}

					snipetStart = i + 1;
				}
			}
			if (snipetStart < diffLines.Count)
				yield return diffLines.GetRange(snipetStart, diffLines.Count - snipetStart);
		}

		private static List<IdentifierDeclaration> FindDeclaredIdentifiersFromSnippet(string javaSnippet)
		{
			List<IdentifierDeclaration> identifierDeclarations = new List<IdentifierDeclaration>();


			var stream = CharStreams.fromString(javaSnippet);
			ITokenSource lexer = new JavaLexer(stream);
			ITokenStream tokens = new CommonTokenStream(lexer);

			int tokenSize = PopulateTokens(tokens);


			var parser = new JavaParser(tokens);
			parser.ErrorHandler = new BailErrorStrategy();
			parser.RemoveErrorListeners();


			int startToken = FindNextToken(tokens).TokenIndex;
			for (; ; )
			{
				IToken startPosition = tokens.LT(1);
				if (startPosition.Type == IntStreamConstants.EOF)
					break;
				if (new[] { ",", ")", "}" }.Contains(startPosition.Text))
				{
					startToken = FindNextToken(tokens, startToken).TokenIndex;
					continue;
				}


				//The order of the parameters, not their placeholder names, determines which parameters are used...
				//https://docs.microsoft.com/en-us/aspnet/core/fundamentals/logging/?view=aspnetcore-5.0#log-message-template
				logger.LogInformation("Start at token {0} (t:{1}, l:{2}, c:{3})", startPosition.Text, startToken, startPosition.Line, startPosition.Column);


				ParserRuleContext tree = FindLongestTree(startToken, tokens, parser);
				//The rule must consume something.
				if (tree != null && tree.Start.TokenIndex <= tree.Stop.TokenIndex)
				{
					int endLine = tree.Stop.Line;

					//matches a full line, probabaly EOF.
					bool isFullLineMatch = false;

					IToken t = FindNextToken(tokens, tree);

					//int nextStartToken = tree.Stop.TokenIndex + 1;
					//tokens.Seek(nextStartToken);
					//nextStartToken = tokens.Index;
#if DEBUG
					if (t.Type == IntStreamConstants.EOF)
					{
						isFullLineMatch = true;
						//Debug.Assert(nextStartToken == tokenSize - 1, "Token stream reads EOF, the index must be the last one.");
					}
					else if (t.Line > endLine)
						isFullLineMatch = true;
#else
					isFullLineMatch = t.Type == IntStreamConstants.EOF || t.Line > endLine;
#endif



					if (isFullLineMatch)
						logger.LogInformation(" {0} matches line {1} in full.", parser.RuleNames[tree.RuleIndex], endLine);
					else
						logger.LogInformation($" {parser.RuleNames[tree.RuleIndex]} match ends at the middle of line {endLine}.");


					if (tree.Start.Line < tree.Stop.Line || isFullLineMatch)
					{
						var identifierCollector = new IdentifierCollector();
						identifierCollector.Visit(tree);
						identifierDeclarations.AddRange(identifierCollector.DeclaredIdentifiers);
					}
					else
						logger.LogInformation("Match is within a line, skip");

					startToken = t.TokenIndex;
				}
				else
				{
					logger.LogInformation(" No rule can be matched.");

					startToken = FindNextToken(tokens, startToken).TokenIndex;
				}
			}
			return identifierDeclarations;
		}

		private static IToken FindNextToken(ITokenStream tokens, [NotNull] ParserRuleContext tree)
		{
			var tokenIndex = tree.Stop.TokenIndex + 1;

			tokens.Seek(tokenIndex);
			return tokens.LT(1);
		}

		private static IToken FindNextToken(ITokenStream tokens, int? currentTokenIndex = null)
		{
			if (currentTokenIndex == null)
				currentTokenIndex = -1;
			tokens.Seek(currentTokenIndex.Value + 1);
			return tokens.LT(1);
		}

		private static ParserRuleContext FindLongestTree(int startIndex, ITokenStream tokens, JavaParser parser)
		{
			Type type = parser.GetType();

			int stopIndex = 0;
			string longestMatchRule = null;
			RuleContext longestTree = null;
			foreach (string ruleName in parser.RuleIndexMap.Keys)
			{
				tokens.Seek(startIndex);
				logger.LogDebug("Try rule {0}...", ruleName);

				try
				{
					var m = type.GetMethod(ruleName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
					Debug.Assert(m != null);
					ParserRuleContext context = (ParserRuleContext)m.Invoke(parser, new object[0]);

					if (context == null)
					{
						logger.LogDebug("{0} is not a match.", ruleName);
					}
					else
					{
						//var tree = parser.classBodyDeclaration();

						logger.LogDebug("{0} produced a full match, stoped at {1}.", ruleName, context.Stop.StopIndex);
						if (context.Stop.StopIndex > stopIndex)
						{
							stopIndex = context.Stop.StopIndex;
							longestMatchRule = ruleName;
							longestTree = context;
						}
					}
				}
				catch (TargetInvocationException e)
				{
					if (e.InnerException is ParseCanceledException)
					{
						RecognitionException recongnitionException = (RecognitionException)e.InnerException.InnerException;
						var tree = recongnitionException.Context;

						if (recongnitionException.OffendingToken.TokenIndex == tokens.Size - 1 && tokens.LA(1) == IntStreamConstants.EOF)
						{
							logger.LogDebug("{0} stoped at the end of input. The input is an incomplete syntax unit.", ruleName);

							Debug.Assert(recongnitionException.OffendingToken.StartIndex >= stopIndex);
							longestMatchRule = ruleName;
							longestTree = tree;
							break;
						}
						else
						{

							logger.LogDebug(" match up to {0}, and IsEmpty={1}.", tree.SourceInterval.b, tree.IsEmpty);
							if (tree.SourceInterval.b > stopIndex)
							{
								stopIndex = tree.SourceInterval.b;
								longestMatchRule = ruleName;
								longestTree = tree;
							}
						}
					}
				}
				catch (ParseCanceledException e)
				{

				}
			}

			if (longestTree == null)
				return null;

			while (longestTree.Parent != null)
			{
				longestTree = longestTree.Parent;
			}
			Debug.Assert(longestTree == null || longestTree.GetType().Name.Contains(longestMatchRule, StringComparison.InvariantCultureIgnoreCase));
			return (ParserRuleContext)longestTree;
		}



		class IdentifierDeclarationInDiff
		{
			public IdentifierDeclaration IdentifierDeclaration { get; set; }
			public int SnippetIndex { get; set; }
		}
	}
}
