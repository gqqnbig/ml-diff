﻿using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using System;
using System.Collections.Generic;
using System.Text;

namespace DiffSyntax.Parser
{
	class IncompleteSnippetStrategy : DefaultErrorStrategy
	{
		public IncompleteSnippetStrategy(bool canFixBeginning, bool canFixEnding)
		{
			this.canFixBeginning = canFixBeginning;
			this.canFixEnding = canFixEnding;
		}

		int firstValidToken = -1;
		int lastValidToken = -1;
		int notLastToken = -1;
		private readonly bool canFixBeginning;
		private readonly bool canFixEnding;

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
						return GetMissingSymbol(recognizer);
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
					return GetMissingSymbol(recognizer);
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

		public override void Sync(Antlr4.Runtime.Parser recognizer)
		{
			//base.Sync(recognizer);
		}
	}
}