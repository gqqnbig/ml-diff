using Antlr4.Runtime;
using DiffSyntax.Antlr;
using DiffSyntax.Parser;
using Microsoft.Extensions.Logging;
using Xunit;
using Xunit.Abstractions;

namespace DiffSyntax.Tests
{
	public class FixedContextTest
	{
		private readonly ILogger logger;

		public FixedContextTest(ITestOutputHelper outputHelper)
		{
			logger = LoggerFactory.Create(builder =>
			{
				builder.AddXunit(outputHelper);
#if DEBUG
				builder.AddDebug();
				builder.SetMinimumLevel(LogLevel.Debug);
#else
				builder.SetMinimumLevel(LogLevel.Warning);
#endif
				// Add other loggers, e.g.: AddConsole, AddDebug, etc.
			}).CreateLogger("FixedContext");
		}

		[Fact]
		public void TestAppendIsBetter()
		{
			string input = "import a;/*";

			var tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input)));
			JavaParser parser = new JavaParser(tokens);

			var t1 = new FixedContext { Context = parser.compilationUnit() };
			t1.SetInput(input, tokens);


			var tokens2 = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input + "*/")));
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

			var tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input)));
			JavaParser parser = new JavaParser(tokens);

			var t1 = new FixedContext { Context = parser.compilationUnit() };
			t1.SetInput(input, tokens);


			var tokens2 = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/*"+input)));
			JavaParser parser2 = new JavaParser(tokens2);

			var t2 = new FixedContext { Context = parser2.compilationUnit() };
			t2.IsBeginningFixed = true;
			t2.SetInput("/*" + input, tokens2);
			t2.CharIndexOffset = 2;

			Assert.True(t2.IsBetterThan(t1), $"Prepend \"/*\" to \"{input}\" is better.");
		}


		[Fact(DisplayName = "Fixing complete snippet is not better")]
		public void TestFixCompleteSnippetThenCompare()
		{
			var analyzer = new DiffAnalyzer(logger);
			string input = @"
/* The Camel subscriber. It bridges messages from reactive streams to Camel routes.*/
public class CamelSubscriber implements Subscriber<Exchange>, Closeable {
private static final Logger LOG = LoggerFactory.getLogger(CamelSubscriber.class);
/* Unbounded as per rule #17. No need to refill. */";
			CommonTokenStream tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input)));
			var tree = analyzer.FindLongestTree(0, tokens, false, true);
			tree.SetInput(input, tokens);


			CommonTokenStream tokens2 = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/*" + input)));
			var tree2 = analyzer.FindLongestTree(0, tokens2, false, false);
			tree2.FixDescription = "Token \"/*\" is missing at the beginning.";
			tree2.IsBeginningFixed = true;
			tree2.CharIndexOffset = 2;
			tree2.SetInput("/*" + input, tokens2);

			Assert.False(tree2.IsBetterThan(tree));
		}
	}
}
