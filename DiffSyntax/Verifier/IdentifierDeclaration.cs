using System;
using System.Diagnostics.CodeAnalysis;

namespace DiffSyntax
{
	public class IdentifierDeclaration : IEquatable<IdentifierDeclaration>
	{

		public string Name { get; set; }

		/// <summary>
		/// Index of the rule where the identifier is extracted.
		/// </summary>
		public int Rule { get; set; }

		/// <summary>
		/// The place where the identifier appears at the input. (token index)
		/// </summary>
		public int InputIndex { get; set; }


		public IdentifierDeclaration(string name, int ruleContext, int inputIndex)
		{
			Name = name;
			Rule = ruleContext;
			InputIndex = inputIndex;
		}

		public bool Equals([AllowNull] IdentifierDeclaration other)
		{
			if (other == null)
				return false;
			return Name == other.Name && Rule == other.Rule;
		}

		public override string ToString()
		{
			return Name + " from Rule " + DiffSyntax.Antlr.JavaParser.ruleNames[Rule];
		}
	}
}
