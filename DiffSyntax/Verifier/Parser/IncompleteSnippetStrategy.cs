using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using System;
using System.Collections.Generic;
using System.Text;
using DiffSyntax.Antlr;
using Microsoft.Extensions.Logging;

namespace DiffSyntax.Parser
{
	public class BailJavaLexer : JavaLexer
	{

		private static readonly ILogger logger = ApplicationLogging.loggerFactory.CreateLogger(nameof(BailJavaLexer));

		public BailJavaLexer(ICharStream input) : base(input) { }

		public override void Recover(LexerNoViableAltException e)
		{
			logger.LogWarning(e.Message);
			throw e;
		}
	}


	public class IncompleteSnippetStrategy : DefaultErrorStrategy
	{
		int firstValidToken = -1;
		int lastValidToken = -1;
		int notLastToken = -1;
		private readonly bool canFixBeginning;
		private readonly bool canFixEnding;
		private readonly FixedContext fixedContext;

		//public bool IsBeginningFixed { get; private set; }
		//public bool IsEndingFixed { get; private set; }

		public IncompleteSnippetStrategy(FixedContext fixedContext, bool canFixBeginning, bool canFixEnding)
		{
			this.fixedContext = fixedContext;
			this.canFixBeginning = canFixBeginning;
			this.canFixEnding = canFixEnding;
		}


		public override IToken RecoverInline(Antlr4.Runtime.Parser recognizer)
		{
			int currentIndex = recognizer.InputStream.Index;


			if (canFixEnding && currentIndex > notLastToken)
			{
				if (lastValidToken == -1)
				{
					recognizer.InputStream.Seek(currentIndex + 1);
					int v = recognizer.InputStream.LA(1);
					if (v == IntStreamConstants.EOF)
						lastValidToken = currentIndex;
					else
						notLastToken = currentIndex;

					recognizer.InputStream.Seek(currentIndex);
				}

				if (currentIndex == lastValidToken)
				{
					if (SingleTokenInsertion(recognizer))
					{
						fixedContext.IsEndingFixed = true;
						return GetMissingSymbol(recognizer);
					}
				}
			}

			if (firstValidToken == -1)
			{
				recognizer.InputStream.Seek(0);
				firstValidToken = recognizer.InputStream.Index;

				recognizer.InputStream.Seek(currentIndex);
			}

			if (currentIndex == firstValidToken && canFixBeginning)
			{
				if (SingleTokenInsertion(recognizer))
				{
					fixedContext.IsBeginningFixed = true;
					return GetMissingSymbol(recognizer);
				}
			}

			throw new InputMismatchException(recognizer);
		}

		public override void Recover(Antlr4.Runtime.Parser recognizer, RecognitionException e)
		{
			for (ParserRuleContext context = recognizer.Context; context != null; context = ((ParserRuleContext)context.Parent))
			{
				context.exception = e;
			}
			throw new ParseCanceledException(e);
		}

		public override void Sync(Antlr4.Runtime.Parser recognizer) { }
	}
}
