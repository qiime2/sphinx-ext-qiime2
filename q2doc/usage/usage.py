import ast
from importlib import import_module

from docutils import nodes
from docutils.parsers.rst import Directive

from qiime2.sdk import usage
from q2cli.core.usage import CLIUsage
from qiime2.plugins import ArtifactAPIUsage


class UsageBlock(nodes.General, nodes.Element):
    pass


class UsageDirective(Directive):
    has_content = True

    def run(self):
        output = []
        output.append(nodes.caption(text="Example"))
        code = "\n".join(self.content)
        env = self.state.document.settings.env
        if not hasattr(env, "usage_blocks"):
            env.usage_blocks = []
        env.usage_blocks.append({"code": code})
        return [UsageBlock()]


def process_usage_blocks(app, doctree, fromdocname):
    env = app.builder.env
    qiime2, usage, drivers = dependencies()
    nodes_and_codes = zip(doctree.traverse(UsageBlock), env.usage_blocks)
    for node, code in nodes_and_codes:
        content = []
        code = code["code"]
        tree = ast.parse(code)
        source = compile(tree, filename="<ast>", mode="exec")
        for use in drivers:
            exec(source)
            record_sources = scope_record_sources(use._scope.records)
            if "action" in record_sources:
                example = use.render()
                example_node = nodes.literal_block(example, example)
                content.append(example_node)
        node.replace_self(content)


def dependencies():
    qiime2 = import_module("qiime2")
    usage = import_module("qiime2.sdk.usage")
    # TODO Return CLIUsage driver
    drivers = (ArtifactAPIUsage(),)
    return qiime2, usage, drivers


def scope_record_sources(records):
    sources = [r.source for r in records.values()]
    return sources




def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(
        UsageBlock,
        html=(lambda s, n: s.visit_admonition(n), lambda s, n: s.depart_admonition(n)),
    )
    app.connect("doctree-resolved", process_usage_blocks)
