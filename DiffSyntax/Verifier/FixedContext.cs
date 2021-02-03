using System;
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


		public bool IsBetterThan(FixedContext other)
		{
			if (Context == null)
				return false;

			if (IsCommentTokenPrepended && other.IsFixedByLexer == false)
			{
				if (Context.Start.Type == IntStreamConstants.EOF)
					return true;

				if (Context.Stop == null) //Unable to determine the stop
					return false;

				if (Context.Stop.StopIndex - 2 > other.Context?.Stop?.StopIndex)
					return true;

				Tokens.Seek(Context.Stop.TokenIndex + 1);
				if (Tokens.LA(1) == IntStreamConstants.EOF) //this matches to the end.
					return true;

				if (Context.exception == null && (other.Context == null || other.Context.exception != null))
					return true;

				return false;
			}

			if (IsCommentTokenAppended && other.IsFixedByLexer == false)
			{
				if (Context.Start.Type == IntStreamConstants.EOF)
					return true;

				if (Context.Stop == null) //Unable to determine the stop
					return false;

				if (Context.Stop.StopIndex - 2 > other.Context?.Stop?.StopIndex)
					return true;

				Tokens.Seek(Context.Stop.TokenIndex + 1);
				if (Tokens.LA(1) == IntStreamConstants.EOF) //this matches to the end.
					return true;

				if (Context.exception == null && (other.Context == null || other.Context.exception != null))
					return true;

				return false;
			}

			throw new NotSupportedException();

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
