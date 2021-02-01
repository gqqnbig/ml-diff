using Antlr4.Runtime;
using System.IO;
using Microsoft.Extensions.Logging;

namespace DiffSyntax.Parser
{
	class ErrorListener : BaseErrorListener
	{
		static readonly ILogger logger = ApplicationLogging.loggerFactory.CreateLogger(nameof(ErrorListener));

		public bool HasError { get; private set; }

		public override void SyntaxError(TextWriter output, IRecognizer recognizer, IToken offendingSymbol, int line, int charPositionInLine, string msg, RecognitionException e)
		{
			HasError = true;
			if (e is NoViableAltException)
			{
			}
			else if (e is InputMismatchException)
			{

			}


			//We are able to recover from the error, ie. insertion at the beginning or the end worked.
			if (e == null)
				logger.LogInformation("line " + line + ":" + charPositionInLine + " " + msg);
		}
	}
}
