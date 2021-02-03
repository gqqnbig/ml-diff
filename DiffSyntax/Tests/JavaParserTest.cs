using Antlr4.Runtime;
using DiffSyntax.Antlr;
using Xunit;

namespace Tests
{
	public class JavaParserTest
	{
		[Fact]
		public void TestSkipComments()
		{

			string input = @"
/* hello world */
int a = 1;";

			var tokens = new CommonTokenStream(new JavaLexer(CharStreams.fromString(input)));
			tokens.Fill();
			tokens.Seek(0);
			var t = tokens.LT(1);
			Assert.Equal(0, t.TokenIndex);
			Assert.True(t.StartIndex > 0, "Although comments are skipped, the char index of the first token should not be 0.");
		}
	}
}
