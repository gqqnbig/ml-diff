using System;
using System.IO;
using System.Diagnostics;
using Microsoft.Extensions.Logging;
using System.Threading.Tasks;
using Antlr4.Runtime;
using DiffSyntax.Antlr;

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
				LabelExamplesFromGuessed(repo);
			}

		}

		private static void LabelExamplesFromGuessed(string repo)
		{
			string baseFolder = @"D:\renaming\data\real";
			logger.LogInformation($"Label examples from {repo}");

			string repoFolder = Path.Join(baseFolder, repo);
			string targetFolder = Path.Join(@"D:\renaming\data\generated\dataset", repo);
			if (Directory.Exists(targetFolder))
			{
				Directory.Delete(targetFolder, true);
				logger.LogInformation($"Deleted existing target folder {targetFolder}.");
			}
			Directory.CreateDirectory(Path.Join(targetFolder, "no"));
			Directory.CreateDirectory(Path.Join(targetFolder, "yes"));

			var diffAnalyzer = new DiffAnalyzer();

			string[] lines = File.ReadAllLines(Path.Join(baseFolder, repo + ".txt"));
			Parallel.ForEach(lines, line =>
			{
				//throw new Exception();
				var parts = line.Split('|');
				var sha = parts[0];
				var extra = parts[1];
				var guessedLabel = parts[2];

				if (guessedLabel == "y" || guessedLabel == "skip")
				{
					var diffPath = Path.Join(repoFolder, sha + ".diff");
					try
					{
						if (diffAnalyzer.CheckIdentifierChanges(diffPath))
						{
							File.Copy(diffPath, Path.Join(targetFolder, "yes", Path.GetFileName(diffPath)));
						}
						else
						{
							File.Copy(diffPath, Path.Join(targetFolder, "no", Path.GetFileName(diffPath)));
						}
					}
					catch (NotSupportedException e)
					{
						logger.LogWarning($"{diffPath} caused error:\n{e.Message}");
					}
					catch (Exception e)
					{
						logger.LogError(new EventId(0), e, $"{diffPath} caused error:\n{e.Message}", new object[0]);
						throw;
					}
				}
			});
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
