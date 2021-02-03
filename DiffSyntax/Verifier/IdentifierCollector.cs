﻿using Antlr4.Runtime.Misc;
using Antlr4.Runtime.Tree;
using System.Collections.Generic;
using DiffSyntax.Antlr;
using static DiffSyntax.Antlr.JavaParser;

namespace DiffSyntax
{
	class IdentifierCollector : JavaParserBaseVisitor<object>
	{
		public List<IdentifierDeclaration> DeclaredIdentifiers { get; private set; } = new List<IdentifierDeclaration>();


		private void VisitDeclaredIdentifier(ITerminalNode identifier, int ruleIndex)
		{

			DeclaredIdentifiers.Add(new IdentifierDeclaration(identifier.GetText(), ruleIndex, identifier.SourceInterval.a));
		}



		//public override object VisitFormalParameter([NotNull] FormalParameterContext context)
		//{
		//	VisitDeclaredIdentifier(context.variableDeclaratorId().IDENTIFIER(), context.RuleIndex);
		//	return null;
		//}

		public override object VisitClassDeclaration([NotNull] ClassDeclarationContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			Visit(context.classBody());
			return null;
		}

		public override object VisitTypeParameter([NotNull] TypeParameterContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			return null;
		}

		public override object VisitEnumDeclaration([NotNull] EnumDeclarationContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			if (context.enumConstants() != null)
				Visit(context.enumConstants());
			if (context.enumBodyDeclarations() != null)
				Visit(context.enumBodyDeclarations());
			return null;
		}

		public override object VisitEnumConstant([NotNull] EnumConstantContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			if (context.classBody() != null)
				Visit(context.classBody());
			return null;
		}

		public override object VisitInterfaceDeclaration([NotNull] InterfaceDeclarationContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			if (context.typeParameters() != null)
				Visit(context.typeParameters());
			Visit(context.interfaceBody());

			return null;
		}

		public override object VisitMethodDeclaration([NotNull] MethodDeclarationContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			Visit(context.formalParameters());
			Visit(context.methodBody());
			return null;
		}

		//Ignore constructorDeclaration

		public override object VisitConstantDeclarator([NotNull] ConstantDeclaratorContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			return null;
		}

		public override object VisitInterfaceMethodDeclaration([NotNull] InterfaceMethodDeclarationContext context)
		{
			if (context.typeParameters() != null)
				Visit(context.typeParameters());
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			Visit(context.methodBody());
			return null;
		}

		public override object VisitVariableDeclaratorId([NotNull] VariableDeclaratorIdContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			return null;
		}

		//Ignore annotation
		//Ignore jumping labels.


		public override object VisitCatchClause([NotNull] CatchClauseContext context)
		{
			VisitDeclaredIdentifier(context.IDENTIFIER(), context.RuleIndex);
			Visit(context.block());
			return null;
		}

		public override object VisitLambdaParameters([NotNull] LambdaParametersContext context)
		{
			throw new System.NotSupportedException("Did't intent to support Java 8");
		}
	}
}