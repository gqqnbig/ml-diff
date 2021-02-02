using System.Diagnostics;
using JetBrains.Annotations;
using Antlr4.Runtime;

namespace DiffSyntax
{
	public class FixedContext
	{
		public ParserRuleContext Context { get; set; }

		//public bool IsAutoFixed { get; set; } = false;
		public bool IsCommentTokenPrepended { get; set; }
		public bool IsCommentTokenAppended { get; set; }

		public bool IsFixedByParser { get; set; }

		public bool IsFixedByLexer => IsCommentTokenPrepended || IsCommentTokenAppended;

		/// <summary>
		/// The number of characters inserted to the beginning of the underlying stream.
		/// </summary>
		public int CharIndexOffset { get; set; }

		public string FixDescription { get; set; }

		public CommonTokenStream Tokens { get; set; }

		public bool IsBetterThan(FixedContext c)
		{
			if(Context!=null && Context.exception==null && Context.Stop!=null && Tokens.GetTokens(Context.Stop.TokenIndex,)


			if (c.Context == null)
				return true;

			//There is an exception causing parser return, and parser cannot determine an end.
			if (c.Context.exception != null && c.Context.Stop == null)
				return true;

			if (Context != null)
			{
				if (Context.Start.Type == IntStreamConstants.EOF ||
					Context.SourceInterval.b - CharIndexOffset > c.Context.SourceInterval.b - CharIndexOffset)
					return true;

				if (Context.exception == null && c.Context.exception != null)
					return true;
			}

			return false;
		}

		public static FixedContext FindBest(params FixedContext[] contexts)
		{
			Debug.Assert(contexts?.Length > 0);

			FixedContext best = contexts[0];
			for (int i = 1; i < contexts.Length; i++)
			{
				if (contexts[i]?.IsBetterThan(best) ?? false)
					best = contexts[i];
			}

			return best;
		}
	}
}
