using Antlr4.Runtime;
using DiffSyntax.Antlr;
using Microsoft.Extensions.Logging;
using Xunit;
using Xunit.Abstractions;
using Xunit.Sdk;
using System.Linq;
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

		/// <summary>
		/// In this test, Antlr cannot determine the Stop of the context without prepending /*.
		/// </summary>
		[Fact]
		public void TestNullStopWithoutFix()
		{
			string input = @"
* file) into a well formed HTML document which can then be sent to XSLT or
* xpath'ed on.
*/
@Component(""tidyMarkup"")
public class TidyMarkupDataFormat extends ServiceSupport implements DataFormat, DataFormatName {
/*";
			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(input);
			if (identifiers.Count == 1)
			{
				Assert.Equal("TidyMarkupDataFormat", identifiers[0].Name);
			}
			else
			{
				throw new XunitException("Expect TidyMarkupDataFormat but actual is "
										 + string.Join(", ", from id in identifiers
															 select id.Name));
			}
		}


		[Fact]
		public void TestMissingEndSymbol()
		{
			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet("int a=1");
			Assert.Equal(1, identifiers.Count);
		}

		[Fact(DisplayName ="Test snippet with 2 block comments with the second one incomplete")]
		public void TestCompleteCommentAndIncompleteComment()
		{
			string input = @"
/**
* View holder object for the GridView
*/
class PodcastViewHolder {

/**
* ImageView holding the Podcast image
";

			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(input);
			Assert.Equal(1, identifiers.Count);
		}

		[Fact(DisplayName = "Test snippet with 2 block comments with the first one incomplete")]
		public void TestCompleteCommentAndIncompleteComment2()
		{
			string javaSnippet = @"
 * @return the associated subscriber
 * @throws IllegalStateException if another consumer is already associated with the given stream name
 */
CamelSubscriber attachCamelConsumer(String name, ReactiveStreamsConsumer consumer);

/**
 * Used by Camel to detach the existing consumer from the given stream.";

			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(javaSnippet);
			Assert.Equal(3, identifiers.Count);
		}

		[Fact]
		public void TestFindLongestTree()
		{
			string javaSnippet = @"
* <p/>
 * Currently, this handler only handles FeedMedia objects, because Feeds and FeedImages are deleted if the download fails.
 */
private class FailedDownloadHandler implements Runnable {

    private DownloadRequest request;
    private DownloadStatus status;";

			CommonTokenStream tokens2 = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString("/*" + javaSnippet)));
			new DiffAnalyzer(logger).FindLongestTree(0, tokens2, false, false);


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
		public void TestUnrecognizedLexerCharacters()
		{
			string input = @"
 *
 * Callers from UI should use {@link #runImmediate(Context)}, as it will guarantee
 * the refresh be run immediately.
 * @param context
 */
public static void runOnce(Context context) {
    Log.d(TAG, ""Run auto update once, as soon as OS allows."");";


			input = @"
# */
int a=1;
/* #";

			//CommonTokenStream tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input)));
			//tokens.Fill();

			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(input);


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
