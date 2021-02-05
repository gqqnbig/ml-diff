using Antlr4.Runtime;
using DiffSyntax.Antlr;
using DiffSyntax.Parser;
using Xunit;

namespace DiffSyntax.Tests
{
	public class JavaParserTest
	{
		[Fact]
		public void TestSkipComments()
		{

			string input = @"
/* hello world */
int a = 1;";

			var tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input)));
			tokens.Fill();
			tokens.Seek(0);
			var t = tokens.LT(1);
			Assert.Equal(0, t.TokenIndex);
			Assert.True(t.StartIndex > 0, "Although comments are skipped, the char index of the first token should not be 0.");
		}

		[Fact]
		public void TestConsumeIncompleteComment()
		{
			var lexer = new BailJavaLexer(CharStreams.fromString("/*"));
			var tokens = new CommonTokenStream(lexer);
			tokens.Fill();
			Assert.True(tokens.Size > 0);
		}

		[Fact]
		public void TestStopNull()
		{
			JavaParser parser = new JavaParser(new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/**/"))));
			var tree = parser.compilationUnit();
			Assert.Equal(IntStreamConstants.EOF, tree.Start.Type);
			Assert.Null(tree.Stop);


			var tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("{ /**/")));
			tokens.Seek(1);
			parser = new JavaParser(tokens);
			tree = parser.compilationUnit();
			Assert.Equal(IntStreamConstants.EOF, tree.Start.Type);
			//If the rule matches nothing, Stop is before Start. If there is nothing before Start, Stop then is null.
			Assert.Equal("{", tree.Stop.Text);
		}

		[Fact]
		public void TestUnableToDetermineStop()
		{
			JavaParser parser = new JavaParser(new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/**/"))));
			var tree = parser.compilationUnit();
			Assert.Equal(IntStreamConstants.EOF, tree.Start.Type);
			Assert.Null(tree.Stop);
		}
	}
}
