using System;
using System.Collections.Generic;
using System.Text;
using Antlr4.Runtime;
using DiffSyntax;
using DiffSyntax.Antlr;
using Xunit;

namespace Tests
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
			t1.Tokens = tokens;


			var tokens2 = new CommonTokenStream(new JavaLexer(CharStreams.fromString(input + "*/")));
			JavaParser parser2 = new JavaParser(tokens2);

			var t2 = new FixedContext { Context = parser2.compilationUnit() };
			t2.IsCommentTokenAppended = true;
			t2.Tokens = tokens2;


			Assert.True(t2.IsBetterThan(t1), $"Append \"*/\" to \"{input}\" is better.");
		}

		[Fact]
		public void TestPrependIsBetter()
		{
			string input = "Redefine this target. */ int a =1;";

			var tokens = new CommonTokenStream(new JavaLexer(CharStreams.fromString(input)));
			JavaParser parser = new JavaParser(tokens);

			var t1 = new FixedContext { Context = parser.compilationUnit() };
			t1.Tokens = tokens;


			var tokens2 = new CommonTokenStream(new JavaLexer(CharStreams.fromString("/*"+input)));
			JavaParser parser2 = new JavaParser(tokens2);

			var t2 = new FixedContext { Context = parser2.compilationUnit() };
			t2.IsCommentTokenPrepended = true;
			t2.Tokens = tokens2;

			Assert.True(t2.IsBetterThan(t1), $"Prepend \"/*\" to \"{input}\" is better.");
		}
	}
}
