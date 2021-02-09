import ast
import os
import operator

from docutils import nodes
from docutils.parsers.rst import Directive

import qiime2
import qiime2.sdk.usage as usage
from qiime2 import Artifact, Metadata
from qiime2.plugins import ArtifactAPIUsage
from q2cli.core.usage import CLIUsage

modules = (qiime2, usage, Artifact, Metadata)


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
    os.chdir(env.srcdir)
    drivers = (ArtifactAPIUsage(), CLIUsage())
    driver_nodes = []
    nodes_ = []
    for use in drivers:
        for ix, (node, code) in enumerate(zip(doctree.traverse(UsageBlock), env.usage_blocks)):
            code = code["code"]
            tree = ast.parse(code)
            source = compile(tree, filename="<ast>", mode="exec")
            processed_records = set()
            exec(source)
            new_records = get_new_records(use._scope.records, processed_records)
            for record in new_records:
                record_source = record.source
                if record_source == "init_data":
                    pass
                elif record_source == "init_metadata":
                    pass
                elif record_source == "get_metadata_column":
                    pass
            if new_records:
                refs = [i.ref for i in new_records]
                processed_records.update(refs)
        example = use.render()
        example_node = nodes.literal_block(example, example)
        nodes_.append(example_node)
    driver_nodes = [*nodes_]
    for node_list, tmp_node in zip(driver_nodes, doctree.traverse(UsageBlock)):
        tmp_node.replace_self(node_list)


def get_new_records(records, processed_records):
    new_records = records.keys() - processed_records
    records = operator.itemgetter(*new_records)(records) if new_records else {}
    return records


def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(
        UsageBlock,
        html=(lambda s, n: s.visit_admonition(n), lambda s, n: s.depart_admonition(n)),
    )
    app.connect("doctree-resolved", process_usage_blocks)
