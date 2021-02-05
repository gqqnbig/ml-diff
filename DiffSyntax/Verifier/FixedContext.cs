using System;
using Antlr4.Runtime;

namespace DiffSyntax
{
	public class FixedContext
	{
		public ParserRuleContext Context { get; set; }

		//public bool IsAutoFixed { get; set; } = false;
		public bool IsBeginningFixed { get; set; }
		public bool IsEndingFixed { get; set; }

		//public bool IsFixedByParser { get; set; }

		public bool IsFixed => IsBeginningFixed || IsEndingFixed;

		/// <summary>
		/// The number of characters inserted to the beginning of the underlying stream.
		/// </summary>
		public int CharIndexOffset { get; set; }

		public string FixDescription { get; set; }

		public CommonTokenStream Tokens { get; private set; }

		public string Input { get; private set; }


		public void SetInput(string input, CommonTokenStream tokens)
		{
			Tokens = tokens;
			Input = input;
		}


		public bool IsBetterThan(FixedContext other)
		{
			if (Context == null)
				return false;

			if (IsBeginningFixed && other.IsFixed == false)
			{
				if (Context.Start.Type == IntStreamConstants.EOF)
					return true;

				if (Context.Stop == null) //this context is unable to determine the stop
					return false;

				//other context is unable to determine stop.
				if (other.Context?.Stop?.StopIndex == null || Context.Stop.StopIndex - 2 > other.Context.Stop.StopIndex)
					return true;

				Tokens.Seek(Context.Stop.TokenIndex + 1);
				if (Tokens.LA(1) == IntStreamConstants.EOF) //this matches to the end.
					return true;

				if (Context.exception == null && (other.Context == null || other.Context.exception != null))
					return true;

				return false;
			}



			if (IsEndingFixed && other.IsFixed == false)
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

			//I have to insert token, but the other can return context in full.
			if (IsFixed && other.Context != null && other.Context.exception == null)
				return false;

			throw new NotSupportedException();
		}

	}
}
