using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using DiffSyntax.Antlr;
using DiffSyntax.Parser;
using Microsoft.Extensions.Logging;

namespace DiffSyntax
{
	public class DiffAnalyzer
	{
		private readonly ILogger logger;


		/// <summary>
		/// Allow to skip up to this number of tokens before starting match. 
		/// </summary>
		private const int SkipInlineTokens = 0;
		//int maxAllowedUnmatchedLines = 2;

		public DiffAnalyzer(ILogger logger = null)
		{
			this.logger = logger ?? ApplicationLogging.loggerFactory.CreateLogger(nameof(DiffAnalyzer));
		}

		public bool CheckIdentifierChanges(string diffPath)
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


				try
				{
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
				catch (FormatException e)
				{
					logger.LogInformation($"Ignore snippet {snippetIndex} of {diffPath}. {e.Message} ");
				}
			}

			if (uniqueInBefore.Count == 1 && uniqueInAfter.Count == 1)
			{
				logger.LogInformation($"This diff only changes one identifier, from {uniqueInBefore[0].IdentifierDeclaration.Name} to {uniqueInAfter[0].IdentifierDeclaration.Name}.");
				return true;
			}
			else if (uniqueInBefore.Count == 0 && uniqueInAfter.Count == 0)
			{
				logger.LogInformation("No identifier changes.");
				return false;
			}
			else
			{
				string b = string.Join(", ", from i in uniqueInBefore
											 select i.IdentifierDeclaration.Name);
				string a = string.Join(", ", from i in uniqueInAfter
											 select i.IdentifierDeclaration.Name);

				logger.LogInformation($"There are multiple identifier changes in this diff.\nBefore: {b}\nAfter: {a}.");
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

		private static bool IsLexerCorrect(CommonTokenStream tokens)
		{
			try
			{
				tokens.Fill();
				return true;
			}
			catch (LexerNoViableAltException)
			{
				return false;
			}
		}


		public List<IdentifierDeclaration> FindDeclaredIdentifiersFromSnippet(string javaSnippet)
		{
			CommonTokenStream tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(javaSnippet)));

			if (IsLexerCorrect(tokens))
				return FindDeclaredIdentifiersFromSnippet(javaSnippet, tokens, false, false);

			tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/*" + javaSnippet)));
			if (IsLexerCorrect(tokens))
			{
				logger.LogInformation("Token \"/*\" is missing at the beginning.");
				return FindDeclaredIdentifiersFromSnippet("/*" + javaSnippet, tokens, true, false);
			}

			tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(javaSnippet + "*/")));
			if (IsLexerCorrect(tokens))
			{
				logger.LogInformation("Token \"*/\" is missing at the end.");
				return FindDeclaredIdentifiersFromSnippet(javaSnippet + "*/", tokens, false, true);
			}

			tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/*" + javaSnippet + "*/")));

			if (IsLexerCorrect(tokens))
			{
				logger.LogInformation("Token \"/*\" is missing at the beginning. Token \"*/\" is missing at the end.");
				return FindDeclaredIdentifiersFromSnippet("/*" + javaSnippet + "*/", tokens, true, true);
			}

			throw new FormatException("The input is not valid Java. Lexer throws error.");
		}

		private List<IdentifierDeclaration> FindDeclaredIdentifiersFromSnippet(string javaSnippet, CommonTokenStream tokens, bool isBeginningFixTried, bool isEndingFixTried)
		{
			//int maxAllowedInlineUnmatch = 1;
			int maxAllowedUnmatchedLines = 2;
			int? lastFailedLine = null;

			List<IdentifierDeclaration> identifierDeclarations = new List<IdentifierDeclaration>();
			int startToken = Helper.FindNextToken(tokens).TokenIndex;
			for (; ; )
			{
				IToken startPosition = tokens.LT(1);
				if (startPosition.Type == IntStreamConstants.EOF)
					break;
				Debug.Assert(lastFailedLine == null || startPosition.Line >= lastFailedLine.Value);
				if (new[] { ",", ")", "}" }.Contains(startPosition.Text) ||
					lastFailedLine != null && startPosition.Line == lastFailedLine.Value)
				{
					startToken = Helper.FindNextToken(tokens, startToken).TokenIndex;
					continue;
				}
				lastFailedLine = null;


				//The order of the parameters, not their placeholder names, determines which parameters are used...
				//https://docs.microsoft.com/en-us/aspnet/core/fundamentals/logging/?view=aspnetcore-5.0#log-message-template
				logger.LogInformation("Start at token {0} (t:{1}, l:{2}, c:{3})", startPosition.Text, startToken, startPosition.Line, startPosition.Column);


				var tree = FindLongestTree(startToken, tokens, isBeginningFixTried, isEndingFixTried);
				FixedContext alternativeTree = null;
				if (isBeginningFixTried == false && javaSnippet.Contains("*/"))
				{
					isBeginningFixTried = true;
					CommonTokenStream tokens2 = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/*" + javaSnippet)));
					alternativeTree = FindLongestTree(0, tokens2, false, false);
					alternativeTree.CharIndexOffset = 2;
					alternativeTree.FixDescription = "Token \"/*\" is missing at the beginning.";
					Debug.Assert(alternativeTree.IsBeginningFixed == false, "FindLongestTree is not allowed to fix beginning.");
					alternativeTree.IsBeginningFixed = true;
					alternativeTree.SetInput("/*" + javaSnippet, tokens2);
				}
				else if (isEndingFixTried == false && javaSnippet.Contains("/*"))
				{
					CommonTokenStream tokens3 = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(javaSnippet + "*/")));
					alternativeTree = FindLongestTree(startToken, tokens3, false, false);
					alternativeTree.FixDescription = "Token \"*/\" is missing at the end.";
					alternativeTree.IsEndingFixed = true;
					alternativeTree.SetInput(javaSnippet + "*/", tokens3);
				}

				if (alternativeTree != null && alternativeTree.IsBetterThan(tree))
					tree = alternativeTree;


				if (tree.Context != null && tree.Context.Start.Type == IntStreamConstants.EOF)
				{
					//Input steam is all comment
					Debug.Assert(tree.Context.Stop == null || tree.Context.Stop.TokenIndex < tree.Context.Start.TokenIndex);
					break;
				}


				//int previousStartToken = startToken;
				bool isTreeUseful = CheckTree(tree.Context, tree.Tokens ?? tokens, identifierDeclarations, ref startToken);
				if (isTreeUseful)
				{
					if (string.IsNullOrEmpty(tree.FixDescription) == false)
						logger.LogInformation(tree.FixDescription);

					if (tree.Tokens != null)
					{
						tokens = tree.Tokens;
						tokens.Fill();
						javaSnippet = tree.Input;
					}


					if (tree.IsBeginningFixed)
						isBeginningFixTried = true;
					if (tree.IsEndingFixed)
						isEndingFixTried = true;
				}
				else
				{
					//if (maxAllowedInlineUnmatch-- > 0)
					//	logger.LogInformation($"Unable to match, advance to next token. maxAllowedUnmatch decreased to {maxAllowedInlineUnmatch}.");
					//else 
					//Do not try to match half way because the first token may be important and change the meaning of the remaining.
					logger.LogInformation($"The first token \"{startPosition.Text}\" at line {startPosition.Line} cannot produce a match.");
					if (maxAllowedUnmatchedLines-- > 0)
					{
						logger.LogInformation($"Advance to next line as I can skip {maxAllowedUnmatchedLines + 1} times.");
						lastFailedLine = startPosition.Line;
						//maxAllowedInlineUnmatch = 1;
					}
					else
						throw new FormatException("Input is invalid. Is it all comments?");
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
		private bool CheckTree(ParserRuleContext tree, CommonTokenStream tokens, List<IdentifierDeclaration> identifierDeclarations, ref int startToken)
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
		public FixedContext FindLongestTree(int startIndex, ITokenStream tokens, bool canFixBeginning, bool canFixEnding)
		{
			FixedContext longestTree = null;

			foreach (string ruleName in JavaParser.ruleNames)
			{
				tokens.Seek(startIndex);

				ErrorListener errorListener = new ErrorListener();
				try
				{
					FixedContext c = new FixedContext();
					JavaParser parser = new JavaParser(tokens);
					parser.RemoveErrorListeners();
					if (canFixBeginning || canFixEnding)
					{
						parser.ErrorHandler = new IncompleteSnippetStrategy(c, canFixBeginning, canFixEnding);
						parser.AddErrorListener(errorListener);
					}
					else
					{
						parser.ErrorHandler = new BailErrorStrategy();
					}


					var m = typeof(JavaParser).GetMethod(ruleName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
					Debug.Assert(m != null);
					c.Context = (ParserRuleContext)m.Invoke(parser, new object[0]);

					if (c.Context == null)
					{
						logger.LogDebug("{0} is not a match.", ruleName);
					}
					else if (c.Context.Start.Type == IntStreamConstants.EOF)
					{
						logger.LogDebug("Input stream is all comment.");
						return c;
					}
					else
					{
						logger.LogDebug("{0} produced a full match, stopped at {1}.", ruleName, c.Context.SourceInterval.b);
						if (longestTree?.Context == null ||
							c.Context.SourceInterval.b > longestTree.Context.SourceInterval.b ||
							//If SourceInterval.b is the same, check if this rule doesn't have exception
							c.Context.SourceInterval.b == longestTree.Context.SourceInterval.b && (c.Context.exception == null || c.IsFixed == false) && (longestTree.Context.exception != null || longestTree.IsFixed))
						{
							longestTree = c;
						}
					}
				}
				catch (TargetInvocationException e)
				{
					if (e.InnerException is ParseCanceledException)
					{
						RecognitionException recognitionException = (RecognitionException)e.InnerException.InnerException;
						ParserRuleContext context = (ParserRuleContext)recognitionException.Context;

						if (recognitionException.OffendingToken.TokenIndex == tokens.Size - 1 && tokens.LA(1) == IntStreamConstants.EOF)
						{
							logger.LogDebug("{0} stopped at the end of input. The input is an incomplete syntax unit.", ruleName);

							Debug.Assert(longestTree?.Context?.Stop == null || recognitionException.OffendingToken.StartIndex >= longestTree.Context.Stop.StopIndex);
							longestTree = new FixedContext { Context = context };
							break;
						}
						else
						{
							logger.LogDebug($"{ruleName} match up to {0}, and IsEmpty={1}.", context.SourceInterval.b, context.IsEmpty);
							//context.SourceInterval.b cannot be null, while context.Stop may be.
							if (longestTree?.Context == null || context.SourceInterval.b > longestTree.Context.SourceInterval.b)
							{
								longestTree = new FixedContext { Context = context };
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



	}


	class IdentifierDeclarationInDiff
	{
		public IdentifierDeclaration IdentifierDeclaration { get; set; }
		public int SnippetIndex { get; set; }
	}
}
