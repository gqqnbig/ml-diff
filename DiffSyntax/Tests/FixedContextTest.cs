using System;
using System.Collections.Generic;
using System.Text;
using Antlr4.Runtime;
using DiffSyntax;
using DiffSyntax.Antlr;
using Xunit;

namespace DiffSyntax.Tests
{
	public class FixedContextTest
	{
		[Fact]
		public void TestAppendIsBetter()
		{
			string input = "import a;/*";

			var tokens = new CommonTokenStream(new JavaLexer(CharStreams.fromString(input)));
			JavaParser parser = new JavaParser(tokens);

			var t1 = new FixedContext { Context = parser.compilationUnit() };
			t1.SetInput(input, tokens);


			var tokens2 = new CommonTokenStream(new JavaLexer(CharStreams.fromString(input + "*/")));
			JavaParser parser2 = new JavaParser(tokens2);

			var t2 = new FixedContext { Context = parser2.compilationUnit() };
			t2.IsEndingFixed = true;
			t2.SetInput(input + "*/", tokens2);


			Assert.True(t2.IsBetterThan(t1), $"Append \"*/\" to \"{input}\" is better.");
		}

		[Fact]
		public void TestPrependIsBetter()
		{
			string input = "Redefine this target. */ int a =1;";

			var tokens = new CommonTokenStream(new JavaLexer(CharStreams.fromString(input)));
			JavaParser parser = new JavaParser(tokens);

			var t1 = new FixedContext { Context = parser.compilationUnit() };
			t1.SetInput(input, tokens);


			var tokens2 = new CommonTokenStream(new JavaLexer(CharStreams.fromString("/*"+input)));
			JavaParser parser2 = new JavaParser(tokens2);

			var t2 = new FixedContext { Context = parser2.compilationUnit() };
			t2.IsBeginningFixed = true;
			t2.SetInput("/*" + input, tokens2);
			t2.CharIndexOffset = 2;

			Assert.True(t2.IsBetterThan(t1), $"Prepend \"/*\" to \"{input}\" is better.");
		}
	}
}
