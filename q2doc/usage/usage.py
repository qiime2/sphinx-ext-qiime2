import ast
import os
import operator
import functools
from enum import Enum
from typing import List, Type

import jinja2
from docutils import nodes
from docutils.parsers.rst import Directive

import qiime2
import qiime2.sdk.usage as usage
from qiime2 import Artifact, Metadata
from qiime2.plugins import ArtifactAPIUsage
from q2cli.core.usage import CLIUsage

modules = (qiime2, usage, Artifact, Metadata)

loader = jinja2.PackageLoader("q2doc.usage", "templates")
jinja_env = jinja2.Environment(loader=loader)


class UsageBlock(nodes.General, nodes.Element):
    def __init__(self, titles=[], examples=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.titles = titles
        self.examples = examples


def visit_usage_node(self, node):
    pass


def depart_usage_node(self, node):
    if not node.titles:
        return
    template = jinja_env.get_template("usage.html")
    rendered = template.render(node=node)
    self.body.append(rendered)


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
        # Use a list to preserve the order
        processed_records = []
        for ix, (node, code) in enumerate(
            zip(doctree.traverse(UsageBlock), env.usage_blocks)
        ):
            # execute code in the block
            current_blocks_nodes = all_nodes[ix]
            code = code["code"]
            tree = ast.parse(code)
            source = compile(tree, filename="<ast>", mode="exec")
            # TODO: validate the ast
            exec(source)
            new_records = get_new_records(use, processed_records)
            nodes_ = (
                records_to_nodes(use, new_records, current_blocks_nodes)
                if new_records
                else []
            )
            if nodes_:
                all_nodes[ix].extend(nodes_)
            update_processed_records(new_records, processed_records)
    for node_list, tmp_node in zip(all_nodes.values(), doctree.traverse(UsageBlock)):
        if node_list:
            tmp_node.replace_self(node_list)


def update_processed_records(new_records, processed_records):
    if new_records:
        refs = [i.ref for i in new_records]
        processed_records.extend(refs)


@functools.singledispatch
def records_to_nodes(use, records, prev_nodes) -> List[Type[nodes.Node]]:
    """Transform ScopeRecords into docutils Nodes."""
    return [nodes.Node]


@records_to_nodes.register(usage.ExecutionUsage)
def _(use, records, prev_nodes):
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
def _(use, records, prev_nodes):
    nodes_ = []
    for record in records:
        source = record.source
        if source == "action":
            example = use.render()
            nodes_.append(UsageBlock(titles=["Command Line"], examples=[example]))
            break
    return nodes_


@records_to_nodes.register(ArtifactAPIUsage)
def _(use, records, prev_nodes):
    nodes_ = []
    for record in records:
        source = record.source
        if source == "action":
            node = prev_nodes[0]
            example = use.render()
            node.titles.append("Artifact API")
            node.examples.append(example)
            break
    return nodes_


def get_new_records(use, processed_records):
    """Select records from the Usage driver's Scope that we haven't seen yet."""
    records = use._get_records()
    new_records = [k for k in records.keys() if k not in processed_records]
    records = operator.itemgetter(*new_records)(records) if new_records else None
    return records


class MetaUsage(Enum):
    execution = usage.ExecutionUsage()
    cli = CLIUsage()
    artifact_api = ArtifactAPIUsage()


def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(UsageBlock, html=(visit_usage_node, depart_usage_node))
    app.connect("doctree-resolved", process_usage_blocks)
