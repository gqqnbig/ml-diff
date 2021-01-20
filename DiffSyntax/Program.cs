using System;
using System.IO;
using System.Diagnostics;
using System.Reflection;
using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using System.Linq;

namespace DiffSyntax
{
	class Program
	{

		static void Main(string[] args)
		{
			string input;
			using (StreamReader sr = new StreamReader(@"D:\renaming\neural network\DiffSyntax\test\FilterExample-0-before.java"))
			{
				input = sr.ReadToEnd();
			}

			var stream = CharStreams.fromString(input);
			ITokenSource lexer = new JavaLexer(stream);


			ITokenStream tokens = new CommonTokenStream(lexer);
			var parser = new JavaParser(tokens);
			parser.ErrorHandler = new BailErrorStrategy();
			parser.RemoveErrorListeners();

			var tree = FindLongestTree(0, tokens, parser);

			var identifierCollector = new IdentifierCollector();
			identifierCollector.Visit(tree);

			
			Console.WriteLine($"Found the following declared identifers: " +
								string.Join(", ", from id in identifierCollector.DeclaredIdentifiers
												  select id.Item1 + " from " + parser.RuleNames[id.Item2])
								+ ".");
		}

		private static RuleContext FindLongestTree(int startIndex, ITokenStream tokens, JavaParser parser)
		{
			Type type = parser.GetType();

			int stopIndex = 0;
			string longestMatchRule = null;
			RuleContext longestTree = null;
			foreach (string ruleName in parser.RuleIndexMap.Keys)
			{
				tokens.Seek(startIndex);
				Console.Write($"Try rule {ruleName}...");

				try
				{
					var m = type.GetMethod(ruleName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
					Debug.Assert(m != null);
					ParserRuleContext context = (ParserRuleContext)m.Invoke(parser, new object[0]);

					if (context == null)
						Console.WriteLine($"{ruleName} is not a match.");
					else
					{
						//var tree = parser.classBodyDeclaration();

						Console.WriteLine($"{ruleName} produced a full match, stoped at {context.Stop.StopIndex}.");
						if (context.Stop.StopIndex > stopIndex)
						{
							stopIndex = context.Stop.StopIndex;
							longestMatchRule = ruleName;
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
							Console.WriteLine($"{ruleName} stoped at the end of input. The input is an incomplete syntax unit.");

							Debug.Assert(recongnitionException.OffendingToken.StartIndex >= stopIndex);
							longestMatchRule = ruleName;
							longestTree = tree;
							break;
						}
						else
						{

							Console.WriteLine($" match up to {tree.SourceInterval.b}, and IsEmpty={tree.IsEmpty}.");
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

			while (longestTree.Parent != null)
			{
				longestTree = longestTree.Parent;
			}
			Debug.Assert(longestTree == null || longestTree.GetType().Name.Contains(longestMatchRule, StringComparison.InvariantCultureIgnoreCase));
			return longestTree;
		}
	}
}
