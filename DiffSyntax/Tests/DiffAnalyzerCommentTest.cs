using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Antlr4.Runtime;
using DiffSyntax.Parser;
using Microsoft.Extensions.Logging;
using Xunit;
using Xunit.Abstractions;
using Xunit.Sdk;

namespace DiffSyntax.Tests
{
	/// <summary>
	/// Test situations involving comments
	/// </summary>
	public class DiffAnalyzerCommentTest
	{
		private readonly ILogger logger;

		public DiffAnalyzerCommentTest(ITestOutputHelper outputHelper)
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


		[Fact(DisplayName = "Test snippet with 2 block comments with the second one incomplete")]
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
		public void TestAllComments1()
		{
			string javaSnippet = @"
 * @return the associated subscriber
 * @throws IllegalStateException if another consumer is already associated with the given stream name
 * Used by Camel to detach the existing consumer from the given stream.";

			Assert.Throws<System.FormatException>(() => new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(javaSnippet));
		}

		[Fact]
		public void TestAllComments2()
		{
			string javaSnippet = @"
*     Supported commands are: <tt>now</tt> for current timestamp,
*     <tt>in.header.xxx</tt> or <tt>header.xxx</tt> to use the Date object in the in header.
*     <tt>out.header.xxx</tt> to use the Date object in the out header.
*     <tt>property.xxx</tt> to use the Date object in the out header.
*     <tt>file</tt> for the last modified timestamp of the file (available with a File consumer).
*     Command accepts offsets such as: <tt>now-24h</tt> or <tt>in.header.xxx+1h</tt> or even <tt>now+1h30m-100</tt>.
* </li>";
			Assert.Throws<System.FormatException>(() => new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(javaSnippet));
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
		public void TestUnrecognizedLexerCharacters()
		{
			string input = @"
# */
int a=1;
/* #";

			//CommonTokenStream tokens = new CommonTokenStream(new BailJavaLexer(CharStreams.fromString(input)));
			//tokens.Fill();

			var identifiers = new DiffAnalyzer(logger).FindDeclaredIdentifiersFromSnippet(input);


		}
	}
}
