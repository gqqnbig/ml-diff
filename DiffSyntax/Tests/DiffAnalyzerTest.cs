using Antlr4.Runtime;
using DiffSyntax.Antlr;
using Microsoft.Extensions.Logging;
using Xunit;
using Xunit.Abstractions;

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
		public void DoSomeTest()
		{
			// Arrange
			// Act
			// Assert
			logger.LogInformation("Hello world!");
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
		public void TestCheckIdentifierChanges(string path)
		{
			new DiffAnalyzer(logger).CheckIdentifierChanges(path);
		}
	}
}
