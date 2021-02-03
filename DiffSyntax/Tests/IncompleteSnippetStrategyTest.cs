using System;
using System.Collections.Generic;
using System.Text;
using Antlr4.Runtime;
using DiffSyntax.Antlr;
using DiffSyntax.Parser;
using Xunit;

namespace DiffSyntax.Tests
{
	public class IncompleteSnippetStrategyTest
	{
		[Fact]
		public void TestEndingFix()
		{

			JavaParser parser = new JavaParser(new CommonTokenStream(new JavaLexer(CharStreams.fromString("int a=1"))));
			parser.RemoveErrorListeners();
			FixedContext context = new FixedContext();
			var errorStrategy = new IncompleteSnippetStrategy(context, true, true);
			parser.ErrorHandler = errorStrategy;
			var tree = parser.blockStatement();

			Assert.True(context.IsEndingFixed);
			Assert.False(context.IsBeginningFixed);
		}

		[Fact]
		public void TestBeginningFix()
		{

			JavaParser parser = new JavaParser(new CommonTokenStream(new JavaLexer(CharStreams.fromString("C1 extends C2 {}"))));
			parser.RemoveErrorListeners();
			FixedContext context = new FixedContext();
			var errorStrategy = new IncompleteSnippetStrategy(context, true, true);
			parser.ErrorHandler = errorStrategy;
			var tree = parser.classDeclaration();

			Assert.True(context.IsBeginningFixed);
			Assert.False(context.IsEndingFixed);
		}
	}
}