using System;
using Xunit;
using DiffSyntax;
using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace Tests
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
		public void TestCheckIdentifierChanges()
		{
			string path = @"D:\renaming\data\generated\dataset\AntennaPod\no\83a6d70387e8df95e04f198ef99f992aef674413.diff";
			new DiffAnalyzer(logger).CheckIdentifierChanges(path);

		}
	}
}
