using Antlr4.Runtime.Misc;
using Antlr4.Runtime.Tree;
using System;
using System.Collections.Generic;
using System.Text;

namespace DiffSyntax
{
	class IdentifierCollector : JavaParserBaseVisitor<object>
	{
		public List<Tuple<string, int>> DeclaredIdentifiers { get; private set; } = new List<Tuple<string, int>>();


		private void VisitDeclaredIdentifier(ITerminalNode identifier, int ruleIndex)
		{
			DeclaredIdentifiers.Add(Tuple.Create(identifier.GetText(), ruleIndex));
		}


		public override object VisitMethodDeclaration([NotNull] JavaParser.MethodDeclarationContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			Visit(context.formalParameters());
			Visit(context.methodBody());
			return null;
		}

		public override object VisitFormalParameter([NotNull] JavaParser.FormalParameterContext context)
		{
			VisitDeclaredIdentifier(context.variableDeclaratorId().IDENTIFIER(), context.RuleIndex);
			return null;
		}


	}
}
