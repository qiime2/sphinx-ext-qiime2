import ast
import functools
import operator
import os
from pathlib import Path
from typing import Tuple, Union

import docutils

import qiime2
import qiime2.sdk.usage as usage
from q2cli.core.usage import CLIUsage
from q2doc.command_block.extension import download_node
from q2doc.usage.nodes import (
    UsageNode,
    UsageExampleNode,
    UsageDataNode,
    UsageMetadataNode,
)
from q2doc.usage.meta_usage import MetaUsage
from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk.usage import ScopeRecord


context = {}


def process_usage_block(use, env):
    # Use a list to preserve the order
    processed_records = []
    for block in env.usage_blocks:
        tree = ast.parse(block['code'])
        block["tree"] = tree
        source = compile(tree, filename="<ast>", mode="exec")
        # TODO: validate the ast
        exec(source)
        new_records = get_new_records(use, processed_records)
        records_to_nodes(use, new_records, block, env)
        update_processed_records(new_records, processed_records)


def process_usage_blocks(app, doctree, _):
    env = app.builder.env
    os.chdir(env.srcdir)
    for use in MetaUsage:
        use = use.value
        process_usage_block(use, env)
    update_nodes(doctree, env)


def update_nodes(doctree, env):
    tree = doctree.traverse(UsageNode)
    for block, tmp_node in zip(env.usage_blocks, tree):
        nodes = block["nodes"]
        tmp_node.replace_self(nodes)


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


def factories_to_nodes(block, env):
    usage_node = block["nodes"].pop()
    root, docname = [Path(p) for p in Path(usage_node.source).parts[-2:]]
    docname = docname.stem
    base = 'https://library.qiime2.org'
    name = f'{usage_node.name}.qza'
    url = f'{base}/{root}/{docname}/{name}'
    id_ = env.new_serialno()
    dl_node = download_node(id_=id_, url=url, saveas=name)
    block["nodes"].append(dl_node)


class FuncVisitor(ast.NodeVisitor):
    names = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.names.append(node.name)


@functools.singledispatch
def records_to_nodes(use, records, block, env) -> None:
    """Transform ScopeRecords into docutils Nodes."""


@records_to_nodes.register(usage.ExecutionUsage)
def execution(use, records, block, env):
    if block["nodes"][0].factory:
        factories_to_nodes(block, env)
    for record in records:
        artifact = record.result
        path = os.path.join(env.srcdir, f'{record.ref}.qza')
        # TODO .save doesn't save where I expected it to...
        if record.source == "init_metadata":
            artifact.save(path)
        elif record.source == "init_data":
            artifact.save(path)


@records_to_nodes.register(CLIUsage)
def cli(use, records, block, env):
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
def artifact_api(use, records, block, env):
    nodes = []
    for record in records:
        source = record.source
        if source == "init_data":
            # TODO Keep track of which example data we've seen?
            nodes.append(docutils.nodes.title(text=record.ref))
            data_node = init_data_node(record)
            nodes.append(data_node)
        elif source == "init_metadata":
            nodes.append(docutils.nodes.title(text=record.ref))
            metadata_node = init_metadata_node(record)
            nodes.append(metadata_node)
        elif source == "action":
            node = block["nodes"][1]
            example = use.render()
            node.titles.append("Artifact API")
            node.examples.append(example)
            break
    block["nodes"].extend(nodes)


def init_data_node(record):
    name = record.ref
    stype = f"'{artifact.type}'"
    setup = f"{name} = qiime2.Artifact.import_data({stype}, '{name}.qza')"
    artifact = MetaUsage.execution.value._get_record(name).result
    node = UsageDataNode(stype, setup)
    return node


def artifact_api_setup(data):
    setup = "Artifact API setup"
    return setup


def init_metadata_node(record):
    name = record.ref
    metadata = MetaUsage.execution.value._get_record(name).result
    setup = f"{name} = qiime2.Metadata.load('{name}.qza)'"
    preview = str(metadata.to_dataframe().head())
    node = UsageMetadataNode(setup, preview)
    return node
