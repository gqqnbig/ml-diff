using Antlr4.Runtime;
using DiffSyntax.Antlr;
using Microsoft.Extensions.Logging;
using Xunit;
using Xunit.Abstractions;
using Xunit.Sdk;
using System.Linq;

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

		[Fact]
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

		[Fact]
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

			CommonTokenStream tokens2 = new CommonTokenStream(new JavaLexer(CharStreams.fromString("/*" + javaSnippet)));
			new DiffAnalyzer(logger).FindLongestTree(0, tokens2, false, false);


		}


		[Theory]
		[InlineData(@"D:\renaming\data\generated\dataset\AntennaPod\no\83a6d70387e8df95e04f198ef99f992aef674413.diff")]
		[InlineData(@"D:\renaming\data\generated\dataset\AntennaPod\no\118d9103c124700d82f5f50e2b8a7b2b8a5cb4ad.diff")]
		[InlineData(@"D:\renaming\data\real\camel\000e09a80874cc6b3ee748504611d4bb45be3483.diff")]
		//[InlineData(@"D:\renaming\data\real\camel\001a5bcbd32d839bb39b7a1ffd52156d55495b85.diff")]
		[InlineData(@"D:\renaming\data\real\camel\041bda6ecc320200f85b9597e8826940f53fd6bd.diff")]
		public void TestCheckIdentifierChanges(string path)
		{
			new DiffAnalyzer(logger).CheckIdentifierChanges(path);
		}
	}
}
