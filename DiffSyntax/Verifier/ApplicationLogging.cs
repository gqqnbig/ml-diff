using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System;
using System.IO;

namespace DiffSyntax
{
	class ApplicationLogging
	{
		public static readonly ILoggerFactory loggerFactory;

		static ApplicationLogging()
		{
			string configFilePath = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(System.AppContext.BaseDirectory), "appsettings.json");
			if (System.IO.File.Exists(configFilePath) == false)
				Console.Error.WriteLine($"{configFilePath} doesn't exist.");
			var builder = new ConfigurationBuilder()
				.SetBasePath(Directory.GetCurrentDirectory())
				.AddJsonFile(configFilePath, optional: true, reloadOnChange: true);
			var configuration = builder.Build();

			loggerFactory = LoggerFactory.Create(builder =>
			{
				builder.AddConfiguration(configuration.GetSection("Logging")).AddSimpleConsole();
			});
		}
	}
}
