using System;
using Xunit;
using DiffSyntax;

namespace Tests
{
	public class UnitTest1
	{
		[Fact]
		public void Test1()
		{
			var identifiers = Program.FindDeclaredIdentifiersFromSnippet("int a=1");
			Assert.Equal(1, identifiers.Count);
		}
	}
}
