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
			var repos = new[]{
//"AntennaPod",
//"baritone",
"camel",
"camunda-bpm-platform",
"dbeaver",
"EhViewer",
"Geyser",
"iceberg",
"Java",
"java-design-patterns",
"jenkins",
"keycloak",
"libgdx",
"Mindustry",
//"NewPipe",
"openapi-generator",
"quarkus",
"Signal-Android",
"spring-petclinic",
"strimzi-kafka-operator",
"testcontainers-java",
"tutorials",
"wiremock"};

			foreach (var repo in repos)
			{
				LabelExamples(@"D:\renaming\data\real\" + repo, @"D:\renaming\data\generated\dataset\" + repo);
			}

		}

		private static void LabelExamples(string folder, string target)
		{
			logger.LogInformation($"Label examples from {folder}");

			if (Directory.Exists(target))
			{
				Directory.Delete(target, true);
				logger.LogInformation($"Deleted existing target folder {target}.");
			}
			Directory.CreateDirectory(target + @"\no");
			Directory.CreateDirectory(target + @"\yes");

			var diffAnalyzer = new DiffAnalyzer();

			foreach (string path in System.IO.Directory.EnumerateFiles(folder, "*.diff", SearchOption.TopDirectoryOnly))
			{
				try
				{
					if (diffAnalyzer.CheckIdentifierChanges(path))
					{
						File.Copy(path, Path.Join(target, "yes", Path.GetFileName(path)));
					}
					else
					{
						File.Copy(path, Path.Join(target, "no", Path.GetFileName(path)));
					}
				}
				catch (NotSupportedException e)
				{
					logger.LogWarning($"{path} caused error:\n{e.Message}");
				}
				catch (Exception e)
				{
					logger.LogError(new EventId(0), e, $"{path} caused error:\n{e.Message}", new object[0]);
					return;
				}
			}
		}

		private static void CheckExamples()
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
				catch (NotSupportedException e)
				{
					logger.LogWarning($"{path} caused error:\n{e.Message}");
				}
				catch (Exception e)
				{
					logger.LogError(new EventId(0), e, $"{path} caused error:\n{e.Message}", new object[0]);
					return;
				}
			}
		}
	}
}
