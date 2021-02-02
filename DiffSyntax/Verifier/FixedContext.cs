using Antlr4.Runtime;

namespace DiffSyntax
{
	public class FixedContext
	{
		public ParserRuleContext Context { get; set; }

		public bool IsAutoFixed { get; set; } = false;

		/// <summary>
		/// The number of characters inserted to the beginning of the underlying stream.
		/// </summary>
		public int CharIndexOffset { get; set; }


		public bool IsBetterThan(FixedContext c)
		{
			if (c.Context == null)
				return true;


			if (Context != null &&
				(Context.Start.Type == IntStreamConstants.EOF ||
				 Context.SourceInterval.b - CharIndexOffset < c.Context.SourceInterval.b - CharIndexOffset))
				return true;

			return false;

		}
	}
}
