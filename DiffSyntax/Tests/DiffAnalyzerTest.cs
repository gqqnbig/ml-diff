using Antlr4.Runtime;
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
		public void TestMissingEndSymbol()
		{
			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet("int a=1");
			Assert.Equal(1, identifiers.Count);
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
		public void TestCheckIdentifierChanges(string path)
		{
			new DiffAnalyzer(logger).CheckIdentifierChanges(path);
		}
	}
}
