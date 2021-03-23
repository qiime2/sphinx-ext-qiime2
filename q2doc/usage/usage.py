import ast
import os
import operator
import functools
from enum import Enum
from typing import Union, Tuple

import docutils

import qiime2
import qiime2.sdk.usage as usage
from q2doc.usage.directive import UsageNode, UsageExampleNode, UsageDataNode
from qiime2.sdk.usage import ScopeRecord
from qiime2 import Artifact, Metadata
from qiime2.plugins import ArtifactAPIUsage
from q2cli.core.usage import CLIUsage
from q2doc.command_block.extension import download_node

modules = (qiime2, usage, Artifact, Metadata)


class MetaUsage(Enum):
    execution = usage.ExecutionUsage()
    cli = CLIUsage()
    artifact_api = ArtifactAPIUsage()


def extract_blocks(doctree, env):
    blocks = []
    tree = doctree.traverse(UsageNode)
    for node, code in zip(tree, env.usage_blocks):
        blocks.append({"code": code["code"], "nodes": [node]})
    return blocks


def process_usage_blocks(app, doctree, _):
    env = app.builder.env
    os.chdir(env.srcdir)
    blocks = extract_blocks(doctree, env)
    for use in MetaUsage:
        use = use.value
        process_usage_block(blocks, use)
    update_nodes(doctree, blocks)


def process_usage_block(blocks, use):
    # Use a list to preserve the order
    processed_records = []
    for block in blocks:
        # Grab code in the current block and execute it.
        code = block["code"]
        tree = ast.parse(code)
        block["tree"] = tree
        source = compile(tree, filename="<ast>", mode="exec")
        # TODO: validate the ast
        exec(source)
        new_records = get_new_records(use, processed_records)
        records_to_nodes(use, new_records, block)
        update_processed_records(new_records, processed_records)


def update_nodes(doctree, blocks):
    tree = doctree.traverse(UsageNode)
    for block, tmp_node in zip(blocks, tree):
        nodes = block["nodes"]
        # Not sure if this check is necessary.
        if nodes:
            tmp_node.replace_self(nodes)


class FuncVisitor(ast.NodeVisitor):
    names = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.names.append(node.name)


def factories_to_nodes(block):
    nodes = []
    # TODO Call factories and save results
    base = "https://library.qiime2.org"
    tree = block["tree"]
    visitor = FuncVisitor()
    visitor.visit(tree)
    for name in visitor.names:
        nodes.append(
            download_node(id_=name, url=f"{base}/{name}", saveas=name)
        )
    block["nodes"] = nodes


@functools.singledispatch
def records_to_nodes(use, records, prev_nodes) -> None:
    """Transform ScopeRecords into docutils Nodes."""
    pass


@records_to_nodes.register(usage.ExecutionUsage)
def execution(use, records, block):
    nodes = []
    if block["nodes"][0].factory:
        factories_to_nodes(block)
    for record in records:
        source = record.source
        result = record.result
        ref = record.ref
        nodes.append(docutils.nodes.title(text=ref))
        setup = block["code"]
        if source == "init_data":
            preview = str(result.type)
        elif source == "init_metadata":
            preview = str(result.to_dataframe().head())
        elif source not in ["action", "get_metadata_column"]:
            return
        else:
            return []
        data_node = UsageDataNode(preview, setup)
        nodes.append(data_node)
    block["nodes"].extend(nodes)


@records_to_nodes.register(CLIUsage)
def cli(use, records, block):
    nodes = []
    for record in records:
        source = record.source
        if source == "action":
            example = "".join(use.render())
            nodes.append(
                UsageExampleNode(titles=["Command Line"], examples=[example])
            )
            break
    block["nodes"].extend(nodes)


@records_to_nodes.register(ArtifactAPIUsage)
def artifact_api(use, records, block):
    nodes = []
    for record in records:
        source = record.source
        if source == "action":
            node = block["nodes"][1]
            example = use.render()
            node.titles.append("Artifact API")
            node.examples.append(example)
            break
    block["nodes"].extend(nodes)


def get_new_records(use, processed_records) -> Union[Tuple[ScopeRecord], None]:
    """Select records from the Usage driver's Scope that we haven't seen yet."""
    records = use._get_records()
    new_records = [k for k in records.keys() if k not in processed_records]
    records = (
        operator.itemgetter(*new_records)(records) if new_records else tuple()
    )
    return records


def update_processed_records(new_records, processed_records):
    refs = [i.ref for i in new_records]
    processed_records.extend(refs)
