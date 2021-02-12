import ast
import os
import operator
import functools
from enum import Enum
from typing import List, Type

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
    all_nodes = {ix: [] for ix, _ in enumerate(env.usage_blocks)}
    for use in MetaUsage:
        use = use.value
        processed_records = []
        for ix, (node, code) in enumerate(zip(doctree.traverse(UsageBlock), env.usage_blocks)):
            # execute code in the block
            code = code["code"]
            tree = ast.parse(code)
            source = compile(tree, filename="<ast>", mode="exec")
            # TODO: validate the ast
            exec(source)
            new_records = get_new_records(use, processed_records)
            nodes_ = records_to_nodes(use, new_records)
            if nodes_:
                all_nodes[ix].extend(nodes_)
            if new_records:
                refs = [i.ref for i in new_records]
                processed_records.extend(refs)
    for node_list, tmp_node in zip(all_nodes.values(), doctree.traverse(UsageBlock)):
        if node_list:
            tmp_node.replace_self(node_list)


@functools.singledispatch
def records_to_nodes(use, records) -> List[Type[nodes.Node]]:
    return [nodes.Node]


@records_to_nodes.register(usage.ExecutionUsage)
def _(use, records):
    nodes_ = []
    for record in records:
        source = record.source
        data = record.result
        record_type = type(record.result)
        if source == "init_data":
            nodes_.append(nodes.title(text="Data"))
            data = str(data.type)
        elif source == "init_metadata":
            nodes_.append(nodes.title(text="Metadata"))
            data = str(data.to_dataframe().head())
        else:
            return []
        nodes_.append(nodes.literal_block(data, data))
    return nodes_


@records_to_nodes.register(CLIUsage)
@records_to_nodes.register(ArtifactAPIUsage)
def _(use, records):
    nodes_ = []
    for record in records:
        source = record.source
        if source == "action":
            result = use.render()
            title = "Action"
            nodes_.append(nodes.title(text=title))
            nodes_.append(nodes.literal_block(result, result))
            break
    return nodes_


def get_new_records(use, processed_records):
    records = use._scope.records
    # Use a list to preserve the order
    new_records = [k for k in records.keys() if k not in processed_records]
    records = operator.itemgetter(*new_records)(records) if new_records else tuple()
    return records


class MetaUsage(Enum):
    execution = usage.ExecutionUsage()
    cli = CLIUsage()
    artifact_api = ArtifactAPIUsage()


def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(
        UsageBlock,
        html=(lambda s, n: s.visit_admonition(n), lambda s, n: s.depart_admonition(n)),
    )
    app.connect("doctree-resolved", process_usage_blocks)
