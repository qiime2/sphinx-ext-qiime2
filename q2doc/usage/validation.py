import ast


class BlockValidator(ast.NodeVisitor):

    def visit_FunctionDef(self, node):
        pass

    def visit_Import(self, node):
        pass

    def visit_ImportFrom(self, node):
        pass
