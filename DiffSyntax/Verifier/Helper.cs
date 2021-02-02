using Antlr4.Runtime;
using Antlr4.Runtime.Misc;
using System;
using System.Collections.Generic;
using System.Text;

namespace DiffSyntax
{
	class Helper
	{
		public static IToken FindNextToken(ITokenStream tokens, [NotNull] ParserRuleContext tree)
		{
			var tokenIndex = tree.Stop.TokenIndex + 1;

			tokens.Seek(tokenIndex);
			return tokens.LT(1);
		}

		public static IToken FindNextToken(ITokenStream tokens, int? currentTokenIndex = null)
		{
			if (currentTokenIndex == null)
				currentTokenIndex = -1;
			tokens.Seek(currentTokenIndex.Value + 1);
			return tokens.LT(1);
		}

	}
}
