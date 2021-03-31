import ast
import functools
import operator
import os
from pathlib import Path
from typing import Tuple, Union

import docutils

import qiime2  # noqa: F401
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


def process_usage_blocks(app, doctree, _):
    env = app.builder.env
    os.chdir(env.srcdir)
    for use in MetaUsage:
        use = use.value
        processed_records = []
        for block in env.usage_blocks:
            tree = ast.parse(block['code'])
            block["tree"] = tree
            source = compile(tree, filename="<ast>", mode="exec")
            # TODO: validate the AST
            exec(source)
            new_records = get_new_records(use, processed_records)
            records_to_nodes(use, new_records, block, env)
            update_processed_records(new_records, processed_records)
    update_nodes(doctree, env)


def update_nodes(doctree, env):
    tree = doctree.traverse(UsageNode)
    for block, tmp_node in zip(env.usage_blocks, tree):
        nodes = block["nodes"]
        tmp_node.replace_self(nodes)


def get_new_records(use, processed_records) -> Union[Tuple[ScopeRecord], None]:
    new_records = tuple()
    records = use._get_records()
    new_record_keys = [k for k in records.keys() if k not in processed_records]
    if new_record_keys:
        new_records = operator.itemgetter(*new_record_keys)(records)
    return new_records


def update_processed_records(new_records, processed_records):
    refs = [i.ref for i in new_records]
    processed_records.extend(refs)


def factories_to_nodes(block, env):
    node = block["nodes"].pop()
    root, docname = [Path(p) for p in Path(node.source).parts[-2:]]
    docname = docname.stem
    base = 'https://library.qiime2.org'
    name = f'{node.name}.qza'
    # These files won't actually exist until their respective init data blocks
    # are evaluated by ExecutionUsage.
    url = f'{base}/{root}/{docname}/{name}'
    id_ = env.new_serialno()
    dl_node = download_node(id_=id_, url=url, saveas=name)
    block["nodes"].append(dl_node)


@functools.singledispatch
def records_to_nodes(use, records, block, env) -> None:
    """Transform ScopeRecords into docutils Nodes."""


@records_to_nodes.register(usage.ExecutionUsage)
def execution(use, records, block, env):
    """Creates download nodes and saves factory results."""
    out_dir = Path(env.srcdir) / Path(env.config.values.get('output-dir')[0])
    if not out_dir.exists():
        out_dir.mkdir()
    if block["nodes"][0].factory:
        factories_to_nodes(block, env)
    for record in records:
        artifact = record.result
        path = os.path.join(out_dir, f'{record.ref}.qza')
        # TODO When running tests, artifacts are saved in the tmp testing dir
        #  *as well as* in this repo.  Prevent saving in the repo.
        if record.source == "init_metadata" or "init_data":
            artifact.save(path)


@records_to_nodes.register(CLIUsage)
def cli(use, records, block, env):
    for record in records:
        if record.source == "action":
            example = "".join(use.render())
            node = UsageExampleNode(
                titles=["Command Line"], examples=[example]
            )
            # Break after seeing the first record created by use.action() since
            # we only need to call use.render() once.
            block["nodes"] = [node]
            break


@records_to_nodes.register(ArtifactAPIUsage)
def artifact_api(use, records, block, env):
    for record in records:
        source = record.source
        if source == "init_data":
            block['nodes'].append(docutils.nodes.title(text=record.ref))
            data_node = init_data_node(record)
            block['nodes'].append(data_node)
        elif source == "init_metadata":
            block['nodes'].append(docutils.nodes.title(text=record.ref))
            metadata_node = init_metadata_node(record)
            block['nodes'].append(metadata_node)
        elif source == "action":
            node = block["nodes"][0]
            example = use.render()
            node.titles.append("Artifact API")
            node.examples.append(example)
            # Break after seeing the first record created by use.action() since
            # we only need to call use.render() once.
            break


def init_data_node(record):
    name = record.ref
    fname = f"{name}.qza"
    artifact = MetaUsage.execution.value._get_record(name).result
    stype = f"{artifact.type}"
    load_statement = f"{name} = qiime2.Artifact.load('{fname}')"
    node = UsageDataNode(stype, load_statement, name=name)
    return node


def init_metadata_node(record):
    name = record.ref
    fname = f"{name}.qza"
    metadata = MetaUsage.execution.value._get_record(name).result
    load_statement = f"{name} = qiime2.Metadata.load('{fname}')"
    metadata_preview = str(metadata.to_dataframe())
    node = UsageMetadataNode(load_statement, metadata_preview, name=name)
    return node
