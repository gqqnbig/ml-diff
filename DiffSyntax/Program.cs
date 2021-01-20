using System;
using System.IO;
using System.Diagnostics;
using System.Reflection;
using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using System.Linq;
using System.Collections.Generic;

namespace DiffSyntax
{
	class Program
	{
		static int PopulateTokens(ITokenStream tokens)
		{
			while (tokens.LA(1) != IntStreamConstants.EOF)
				tokens.Consume();

			Debug.Assert(tokens.Index == tokens.Size - 1);
			return tokens.Size;

		}


		static void Main(string[] args)
		{
			List<string> lines = new List<string>();
			using (StreamReader sr = new StreamReader(@"D:\renaming\neural network\DiffSyntax\test\FilterExample-4.diff"))
			{
				while (sr.EndOfStream == false)
					lines.Add(sr.ReadLine());
			}

			var uniqueInBefore = new List<IdentifierDeclarationInDiff>();
			var unqiueInAfter = new List<IdentifierDeclarationInDiff>();

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

				unqiueInAfter.AddRange(from d in ua
									   select new IdentifierDeclarationInDiff { IdentifierDeclaration = d, SnippetIndex = snippetIndex });

				//Console.WriteLine($"Found the following declared identifers: " +
				//			string.Join(", ", from id in identifierCollector.DeclaredIdentifiers
				//							  select id.Name + " from " + parser.RuleNames[id.Rule])
				//			+ ".");

			}

			if (uniqueInBefore.Count == 1 && unqiueInAfter.Count == 1)
			{
				Console.WriteLine($"This diff only changes one identifier, from {uniqueInBefore[0].IdentifierDeclaration.Name} to {unqiueInAfter[0].IdentifierDeclaration.Name}.");
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


			for (int startToken = 0; startToken < tokenSize;)
			{
				tokens.Seek(startToken);
				startToken = tokens.Index;

				IToken startPosition = tokens.LT(1);
				if (startPosition.Type == IntStreamConstants.EOF)
					break;
				Console.Write($"Start at token {startPosition.Text} (t:{startToken}, l:{startPosition.Line}, c:{startPosition.Column})");


				var tree = FindLongestTree(startToken, tokens, parser);
				//The rule must consume something.
				if (tree != null && tree.Start.TokenIndex <= tree.Stop.TokenIndex)
				{
					int endLine = tree.Stop.Line;

					//matches a full line, probabaly EOF.
					bool isFullLineMatch = false;

					int nextStartToken = tree.Stop.TokenIndex + 1;
					tokens.Seek(nextStartToken);
					nextStartToken = tokens.Index;
					if (tokens.LA(1) == IntStreamConstants.EOF)
					{
						isFullLineMatch = true;
						nextStartToken = tokenSize;
					}
					else if (tokens.LT(1).Line > endLine)
						isFullLineMatch = true;


					if (isFullLineMatch)
						Console.WriteLine($" {parser.RuleNames[tree.RuleIndex]} matches line {endLine} in full.");
					else
						Console.WriteLine($" {parser.RuleNames[tree.RuleIndex]} match ends at the middle of line {endLine}.");


					if (tree.Start.Line < tree.Stop.Line || isFullLineMatch)
					{
						var identifierCollector = new IdentifierCollector();
						identifierCollector.Visit(tree);
						identifierDeclarations.AddRange(identifierCollector.DeclaredIdentifiers);
					}
					else
						Console.WriteLine("Match is within a line, skip");

					startToken = nextStartToken;
				}
				else
				{
					Console.WriteLine(" No rule can be matched.");
					startToken++;
				}
			}
			return identifierDeclarations;
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
				//Console.Write($"Try rule {ruleName}...");

				try
				{
					var m = type.GetMethod(ruleName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
					Debug.Assert(m != null);
					ParserRuleContext context = (ParserRuleContext)m.Invoke(parser, new object[0]);

					if (context == null)
					{
						//Console.WriteLine($"{ruleName} is not a match.");
					}
					else
					{
						//var tree = parser.classBodyDeclaration();

						//Console.WriteLine($"{ruleName} produced a full match, stoped at {context.Stop.StopIndex}.");
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
							//Console.WriteLine($"{ruleName} stoped at the end of input. The input is an incomplete syntax unit.");

							Debug.Assert(recongnitionException.OffendingToken.StartIndex >= stopIndex);
							longestMatchRule = ruleName;
							longestTree = tree;
							break;
						}
						else
						{

							//Console.WriteLine($" match up to {tree.SourceInterval.b}, and IsEmpty={tree.IsEmpty}.");
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
