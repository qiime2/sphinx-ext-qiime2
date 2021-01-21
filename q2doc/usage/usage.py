import ast

import docutils
from docutils.parsers.rst import Directive

from q2cli.core.usage import CLIUsage


class UsageBlock(docutils.nodes.General, docutils.nodes.Element):
    pass


class UsageDirective(Directive):
    has_content = True

    def run(self):
        output = []
        output.append(docutils.nodes.caption(text="Example"))
        code = "\n".join(self.content)
        env = self.state.document.settings.env
        if not hasattr(env, "usage_blocks"):
            env.usage_blocks = []
        env.usage_blocks.append({"code": code})
        return [UsageBlock()]


def process_usage_blocks(app, doctree, fromdocname):
    use = CLIUsage()
    exec("from qiime2.sdk.usage import "
         "UsageAction, UsageInputs, UsageOutputNames")
    env = app.builder.env
    nodes_and_codes = zip(doctree.traverse(UsageBlock), env.usage_blocks)
    for node, code in nodes_and_codes:
        code = code["code"]
        content = []
        tree = ast.parse(code)
        exec(code)


def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(
        UsageBlock,
        html=(lambda s, n: s.visit_admonition(n), lambda s, n: s.depart_admonition(n)),
    )
    app.connect("doctree-resolved", process_usage_blocks)
