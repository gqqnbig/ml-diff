using System;
using System.IO;
using Antlr4.Runtime;
using Antlr4.Runtime.Misc;

namespace DiffSyntax
{
	class Program
	{

		static void Main(string[] args)
		{
			string content;
			using (StreamReader sr = new StreamReader(@"D:\renaming\neural network\DiffSyntax\test\FilterExample-0-before.java"))
			{
				content = sr.ReadToEnd();
			}

			var stream = CharStreams.fromString(content);
			ITokenSource lexer = new JavaLexer(stream);

			ITokenStream tokens = new CommonTokenStream(lexer);
			var parser = new JavaParser(tokens);
			parser.ErrorHandler = new BailErrorStrategy();

			foreach(string ruleName in parser.RuleIndexMap.Keys)
			{
				Console.WriteLine($"Try rule {ruleName}...");
				int ruleIndex = parser.RuleIndexMap[ruleName];

				try
				{
					var context = parser.GetInvokingContext(ruleIndex);
					//var tree = parser.classBodyDeclaration();

					Console.WriteLine($"{ruleName} produced a full match.");
				}
				catch (ParseCanceledException e)
				{
					var tree = ((RecognitionException)e.InnerException).Context;
					if (((RecognitionException)e.InnerException).OffendingToken.StartIndex == content.Length)
					{
						Console.WriteLine($"{ruleName} stoped at the end of input. The input is an incomplete syntax unit.");
						break;
					}
					else
					{

						//The chosen context is incorrect. Let's try the next one.

					}
				}
			}

//			var identifierCollector = new IdentifierCollector();
//			Action<JavaParser>[] matchSequences = {
//p => identifierCollector.Visit(p.compilationUnit()),
//p => identifierCollector.Visit(p.typeDeclaration()),
//p => identifierCollector.Visit(p.classDeclaration()),
//p => identifierCollector.Visit(p.enumDeclaration()),
//p => identifierCollector.Visit(p.enumConstants()),
//p => identifierCollector.Visit(p.enumConstant()),
//p => identifierCollector.Visit(p.enumBodyDeclarations()),
//p => identifierCollector.Visit(p.interfaceDeclaration()),
//p => identifierCollector.Visit(p.classBody()),
//p => identifierCollector.Visit(p.interfaceBody()),
//p => identifierCollector.Visit(p.classBodyDeclaration()),
//// p => identifierCollector.Visit(p.memberDeclaration()), // memberDeclaration is an alias of a group of rules.
//p => identifierCollector.Visit(p.methodDeclaration()),
//p => identifierCollector.Visit(p.methodBody()),
//p => identifierCollector.Visit(p.genericMethodDeclaration()),
//p => identifierCollector.Visit(p.genericConstructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.interfaceBodyDeclaration()),
//// p => identifierCollector.Visit(p.interfaceMemberDeclaration()), // interfaceMemberDeclaration is an alias of a group of rules.
//p => identifierCollector.Visit(p.constDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),
//p => identifierCollector.Visit(p.constructorDeclaration()),

			//			};

		}
	}
}
