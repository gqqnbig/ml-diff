using System;
using System.IO;
using System.Diagnostics;
using System.Reflection;
using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using System.Linq;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using DiffSyntax.Parser;

namespace DiffSyntax
{
	public class Program
	{
		private static readonly ILogger logger = ApplicationLogging.loggerFactory.CreateLogger(nameof(Program));

		static void Main(string[] args)
		{
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

		public static List<IdentifierDeclaration> FindDeclaredIdentifiersFromSnippet(string javaSnippet)
		{
			List<IdentifierDeclaration> identifierDeclarations = new List<IdentifierDeclaration>();

			CommonTokenStream tokens = new CommonTokenStream(new JavaLexer(CharStreams.fromString(javaSnippet)));


			bool isBeginningFixTried = false;
			bool isEndingFixTried = false;
			int insertedTokens = 0; //follow single insertion rule.

			int startToken = Helper.FindNextToken(tokens).TokenIndex;
			for (; ; )
			{
				IToken startPosition = tokens.LT(1);
				if (startPosition.Type == IntStreamConstants.EOF)
					break;
				if (new[] { ",", ")", "}" }.Contains(startPosition.Text))
				{
					startToken = Helper.FindNextToken(tokens, startToken).TokenIndex;
					continue;
				}


				//The order of the parameters, not their placeholder names, determines which parameters are used...
				//https://docs.microsoft.com/en-us/aspnet/core/fundamentals/logging/?view=aspnetcore-5.0#log-message-template
				logger.LogInformation("Start at token {0} (t:{1}, l:{2}, c:{3})", startPosition.Text, startToken, startPosition.Line, startPosition.Column);


				var tree = FindLongestTree(startToken, tokens, insertedTokens == 0, insertedTokens == 0);
				if (insertedTokens == 0 && isBeginningFixTried == false)
				{
					isBeginningFixTried = true;
					CommonTokenStream tokens2 = new CommonTokenStream(new JavaLexer(CharStreams.fromString("/*" + javaSnippet)));
					var tree2 = FindLongestTree(0, tokens2, false, false);
					tree2.CharIndexOffset = 2;
					Debug.Assert(tree2.Context == null || tree2.Context.SourceInterval.b < 1, "No auto fixing is allowed, the parsed tree should have no error.");
					if (tree2.IsBetterThan(tree))
					{
						logger.LogInformation("Token \"/*\" is missing at the beginning.");
						tree = tree2;

						javaSnippet = "/*" + javaSnippet;
						tokens = new CommonTokenStream(new JavaLexer(CharStreams.fromString(javaSnippet)));

						insertedTokens++;
					}
				}

				if (tree.Context != null && tree.Context.Start.Type == IntStreamConstants.EOF)
				{
					//Input steam is all comment
					Debug.Assert(tree.Context.Stop == null);
					break;
				}
				else
				{
					int previousStartToken = startToken;
					bool isTreeUseful = CheckTree(tree.Context, tokens, identifierDeclarations, ref startToken);
					if (isTreeUseful && tree.IsAutoFixed)
					{
						insertedTokens++;
					}
					else if (isTreeUseful == false && isEndingFixTried == false && insertedTokens == 0)
					{
						isEndingFixTried = true;
						CommonTokenStream tokens2 = new CommonTokenStream(new JavaLexer(CharStreams.fromString(javaSnippet + "*/")));
						var tree2 = FindLongestTree(previousStartToken, tokens2, false, false);

						if (tree2.IsBetterThan(tree))
						{
							logger.LogInformation("Token \"*/\" is missing at the end.");
							tree = tree2;

							javaSnippet = javaSnippet + "*/";
							tokens = new CommonTokenStream(new JavaLexer(CharStreams.fromString(javaSnippet)));

							insertedTokens++;

							startToken = previousStartToken;
							CheckTree(tree.Context, tokens, identifierDeclarations, ref startToken);
						}
					}
				}
			}
			return identifierDeclarations;
		}

		/// <summary>
		/// 
		/// </summary>
		/// <param name="tree"></param>
		/// <param name="tokens"></param>
		/// <param name="identifierDeclarations"></param>
		/// <param name="startToken"></param>
		private static bool CheckTree(ParserRuleContext tree, CommonTokenStream tokens, List<IdentifierDeclaration> identifierDeclarations, ref int startToken)
		{
			if (tree != null && tree.Start.TokenIndex <= tree.Stop?.TokenIndex) //The rule must consume something.
			{
				IToken t = Helper.FindNextToken(tokens, tree);

				int endLine = tree.Stop.Line;

				bool isFullLineMatch = t.Type == IntStreamConstants.EOF || t.Line > endLine;

				if (isFullLineMatch)
					logger.LogInformation("{0} matches line {1} in full.", JavaParser.ruleNames[tree.RuleIndex], endLine);
				else
					logger.LogInformation($" {JavaParser.ruleNames[tree.RuleIndex]} match ends at the middle of line {endLine}.");

				bool isTreeUseful = false;
				if (tree.Start.Line < tree.Stop.Line || isFullLineMatch)
				{
					var identifierCollector = new IdentifierCollector();
					identifierCollector.Visit(tree);
					identifierDeclarations.AddRange(identifierCollector.DeclaredIdentifiers);

					isTreeUseful = true;
				}
				else
					logger.LogInformation("Match is within a line, skip");

				startToken = t.TokenIndex;
				return isTreeUseful;
			}
			else
			{
				logger.LogInformation("No rule can be matched.");

				startToken = Helper.FindNextToken(tokens, startToken).TokenIndex;
				return false;
			}
		}


		[return: NotNull]
		private static FixedContext FindLongestTree(int startIndex, ITokenStream tokens, bool canFixBeginning, bool canFixEnding)
		{
			FixedContext longestTree = new FixedContext();

			foreach (string ruleName in JavaParser.ruleNames)
			{
				tokens.Seek(startIndex);

				ErrorListener errorListener = new ErrorListener();
				try
				{
					JavaParser parser = new JavaParser(tokens);
					parser.RemoveErrorListeners();
					if (canFixBeginning || canFixEnding)
					{
						parser.ErrorHandler = new IncompleteSnippetStrategy(canFixBeginning, canFixEnding);
						parser.AddErrorListener(errorListener);
					}
					else
					{
						parser.ErrorHandler = new BailErrorStrategy();
					}


					var m = typeof(JavaParser).GetMethod(ruleName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
					Debug.Assert(m != null);
					ParserRuleContext context = (ParserRuleContext)m.Invoke(parser, new object[0]);

					if (context == null)
					{
						logger.LogDebug("{0} is not a match.", ruleName);
					}
					else if (context.Start.Type == IntStreamConstants.EOF)
					{
						logger.LogDebug("Input stream is all comment.");
						return new FixedContext { Context = context };
					}
					else
					{
						logger.LogDebug("{0} produced a full match, stoped at {1}.", ruleName, context.SourceInterval.b);
						if (longestTree.Context == null || context.SourceInterval.b > longestTree.Context.SourceInterval.b)
						{
							longestTree.Context = context;
						}
					}
				}
				catch (TargetInvocationException e)
				{
					if (e.InnerException is ParseCanceledException)
					{
						RecognitionException recongnitionException = (RecognitionException)e.InnerException.InnerException;
						ParserRuleContext context = (ParserRuleContext)recongnitionException.Context;

						if (recongnitionException.OffendingToken.TokenIndex == tokens.Size - 1 && tokens.LA(1) == IntStreamConstants.EOF)
						{
							logger.LogDebug("{0} stoped at the end of input. The input is an incomplete syntax unit.", ruleName);

							Debug.Assert(recongnitionException.OffendingToken.StartIndex >= longestTree.Context?.Stop.StopIndex);
							longestTree.Context = context;
							break;
						}
						else
						{
							logger.LogDebug($"{ruleName} match up to {0}, and IsEmpty={1}.", context.SourceInterval.b, context.IsEmpty);
							//context.SourceInterval.b cannot be null, while context.Stop may be.
							if (longestTree.Context == null || context.SourceInterval.b > longestTree.Context.SourceInterval.b)
							{
								longestTree.Context = context;
							}
						}
					}
				}
				catch (ParseCanceledException e) { }
			}

			if (longestTree == null)
				return new FixedContext();

			while (longestTree.Context.Parent != null)
			{
				longestTree.Context = (ParserRuleContext)longestTree.Context.Parent;
			}
			return longestTree;
		}



		class IdentifierDeclarationInDiff
		{
			public IdentifierDeclaration IdentifierDeclaration { get; set; }
			public int SnippetIndex { get; set; }
		}
	}
}
