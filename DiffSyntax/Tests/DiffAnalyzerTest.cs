using Antlr4.Runtime;
using DiffSyntax.Antlr;
using Microsoft.Extensions.Logging;
using Xunit;
using Xunit.Abstractions;
using DiffSyntax.Parser;

namespace DiffSyntax.Tests
{
	public class DiffAnalyzerTest
	{
		private readonly ILogger logger;

		public DiffAnalyzerTest(ITestOutputHelper outputHelper)
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
			}).CreateLogger("DiffAnalyzer");
		}

		[Fact]
		public void TestFindLongestTreeLikeEnum()
		{
			string input = "sqlQuery, Statement.RETURN_GENERATED_KEYS)";

			var tree = new DiffAnalyzer(logger).FindLongestTree(0, new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input))), false, false);
			Assert.NotEqual("enumConstants", JavaParser.ruleNames[tree.Context.RuleIndex]);
		}



		[Fact]
		public void TestMissingEndSymbol()
		{
			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet("int a=1");
			Assert.Equal(1, identifiers.Count);
		}

		[Fact]
		public void TestAmbiguousInput()
		{
			new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet("a,b,");
		}


		[Fact]
		public void TestNotSupportJava8()
		{
			string input = @"
public interface TimeClient {
    default ZonedDateTime getZonedDateTime(String zoneString) {
        return ZonedDateTime.of(getLocalDateTime(), getZoneId(zoneString));
    }
}";
			Assert.Throws<System.NotSupportedException>(() => new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(input));
		}

		[Fact]
		public void TestSkipToNextLine()
		{
			string input = @"
throws UnsupportedEncodingException, URISyntaxException {
final DefaultMessage message = new DefaultMessage(camelContext);

assertEquals("""", RestProducer.createQueryParameters(""param={param?}"", message));
}";
			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(input);
			//Assert.Equal(1, identifiers.Count);


			Assert.Collection(identifiers, _ => { });
		}



		[Fact]
		public void TestFindLongestTreeInsertAtEnd()
		{
			var analyzer = new DiffAnalyzer(logger);
			string input = @"/**
* The Camel subscriber. It bridges messages from reactive streams to Camel routes.
*/
public class CamelSubscriber implements Subscriber<Exchange>, Closeable {

private static final Logger LOG = LoggerFactory.getLogger(CamelSubscriber.class);

/**
 * Unbounded as per rule #17. No need to refill.*/";
			CommonTokenStream tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input)));
			var tree = analyzer.FindLongestTree(0, tokens, false, true);
			tree.SetInput(input, tokens);
			Assert.True(tree.IsEndingFixed, "Expect to insert } at the end.");
			Assert.False(string.IsNullOrEmpty(tree.FixDescription));
		}

		[Theory]
		[InlineData(@"D:\renaming\data\generated\dataset\AntennaPod\no\83a6d70387e8df95e04f198ef99f992aef674413.diff")]
		[InlineData(@"D:\renaming\data\generated\dataset\AntennaPod\no\118d9103c124700d82f5f50e2b8a7b2b8a5cb4ad.diff")]
		[InlineData(@"D:\renaming\data\real\camel\000e09a80874cc6b3ee748504611d4bb45be3483.diff")]
		[InlineData(@"D:\renaming\data\real\camel\041bda6ecc320200f85b9597e8826940f53fd6bd.diff")]
		[InlineData(@"D:\renaming\data\real\camel\44883d06903d1cf6d034917e123ce45f21f504d4.diff")]
		[InlineData(@"D:\renaming\data\real\AntennaPod\1b24b0943284d49789754d35d3835be6ded7755d.diff")]
		[InlineData(@"D:\renaming\data\real\camel\00eb3707a0806623a2af228924e26e1184581f00.diff")]
		[InlineData(@"D:\renaming\data\real\dbeaver\f491904b794212ab8d598c06cb8b44dc04ffb5da.diff")]
		[InlineData(@"D:\renaming\data\real\dbeaver\f100c38f0ca6448d52ab82a93676648eb781f46b.diff")]
		[InlineData(@"D:\renaming\data\real\jenkins\304de19e73886c49593c654d14c13448ea97816f.diff")]
		public void TestCheckIdentifierChanges(string path)
		{
			new DiffAnalyzer(logger).CheckIdentifierChanges(path);
		}
	}
}
