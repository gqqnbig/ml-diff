using System;
using System.IO;
using System.Diagnostics;
using Antlr4.Runtime;
using DiffSyntax.Antlr;
using Microsoft.Extensions.Logging;

namespace DiffSyntax
{
	public class Program
	{
		private static readonly ILogger logger = ApplicationLogging.loggerFactory.CreateLogger(nameof(Program));


		static void Main(string[] args)
		{
			var diffAnalyzer = new DiffAnalyzer();

			foreach (string path in System.IO.Directory.EnumerateFiles(@"D:\renaming\data\generated\dataset", "*.diff", SearchOption.AllDirectories))
			{
				string label = Path.GetFileName(Path.GetDirectoryName(path));
				Trace.Assert(label.Equals("yes", StringComparison.OrdinalIgnoreCase) || label.Equals("no", StringComparison.OrdinalIgnoreCase));

				try
				{
					if (diffAnalyzer.CheckIdentifierChanges(path) == label.Equals("yes", StringComparison.OrdinalIgnoreCase))
					{
						Console.WriteLine($"{path} is good");
					}
					else
					{
						Console.WriteLine($"The label of {path} is {label}, but syntax analysis doesn't agree");
					}
				}
				catch (Exception e)
				{
					logger.LogError(new EventId(0), e, $"{path} caused error:\n{e.Message}", new object[0]);
					throw;
				}
			}
		}


	}
}
