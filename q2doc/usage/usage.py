import ast
import functools
import operator
import os
import re
from pathlib import Path
from typing import Tuple, Union

from sphinx.util import logging

import qiime2  # noqa: F401
import pandas as pd  # noqa: F401
from qiime2 import Artifact, Metadata  # noqa: F401
import qiime2.sdk.usage as usage
from q2cli.core.usage import CLIUsage
from q2doc.usage.nodes import (
    UsageNode,
    UsageExampleNode,
    UsageDataNode,
    FactoryNode,
)
from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk.usage import ScopeRecord

from .utils import get_docname
from .validation import BlockValidator

logger = logging.getLogger(__name__)


def process_usage_blocks(app, doctree, _):
    env = app.builder.env
    os.chdir(env.srcdir)
    for k, driver in env.drivers.items():
        # ensure a new instance for each doc
        use = driver() if isinstance(driver, type) else driver.__class__()
        env.drivers[k] = use
        processed_records = []
        for block in env.usage_blocks:
            tree = ast.parse(block['code'])
            block["tree"] = tree
            source = compile(tree, filename="<ast>", mode="exec")
            exec(source)
            new_records = get_new_records(use, processed_records)
            records_to_nodes(use, new_records, block, env)
            processed_records.extend(new_records)
    update_nodes(doctree, env)


def update_nodes(doctree, env):
    for block, node in zip(env.usage_blocks, doctree.traverse(UsageNode)):
        nodes = block["nodes"]
        node.replace_self(nodes)
    for node in doctree.traverse(UsageExampleNode):
        # Tack imports onto the first Example node.
        node.artifact_api = node.prelude()
        break
    for node in doctree.traverse(FactoryNode):
        ref = node.ref
        try:
            result = env.drivers['exc_use']._get_record(ref).result
            if isinstance(result, qiime2.metadata.metadata.Metadata):
                metadata_preview = str(result.to_dataframe())
                node.preview = metadata_preview
        except KeyError as e:
            logger.warning(
                f"Factory `{ref}` is not used in any Usage examples: {e}"
            )


def get_new_records(use, processed_records):
    records = use._get_records().values()
    new_records = [r for r in records if r not in processed_records]
    return new_records or []


def factories_to_nodes(block, env):
    node = block["nodes"].pop()
    root, doc_name = get_docname(node)
    base = env.config.base_url.rstrip('/')
    name = f'{node.name}.qza'
    # These files won't actually exist until their respective init data blocks
    # are evaluated by ExecutionUsage.
    relative_url = f'results/{name}'
    absolute_url = f'{base}/{doc_name}/{relative_url}'
    factory_node = FactoryNode(
        relative_url=relative_url,
        absolute_url=absolute_url,
        saveas=name,
        ref=node.name,
    )
    block["nodes"].append(factory_node)


@functools.singledispatch
def records_to_nodes(use, records, block, env) -> None:
    """Transform ScopeRecords into docutils Nodes."""


@records_to_nodes.register(usage.DiagnosticUsage)
def diagnostic(use, records, block, env):
    validator = BlockValidator()
    validator.visit(block['tree'])


@records_to_nodes.register(usage.ExecutionUsage)
def execution(use, records, block, env):
    """Creates download nodes and saves factory results."""
    node = block["nodes"][0]
    if node.factory:
        # TODO When factories that rely on an object that is imported somewhere
        #  in a usage black are called, they fail.  Current workaround can be
        #  in examples.rst is to import requirements in the factory body.
        factories_to_nodes(block, env)
    for record in records:
        artifact = record.result
        out_dir = Path(env.app.outdir) / node.docname / 'results'
        if not out_dir.exists():
            out_dir.mkdir(parents=True)
        path = os.path.join(out_dir, f'{record.ref}.qza')
        if record.source in ["init_metadata", "init_data"]:
            artifact.save(path)


@records_to_nodes.register(CLIUsage)
def cli(use, records, block, env):
    for record in records:
        if record.source == "action":
            rendered = "\n\n".join(use.render())
            example = remove_rendered(rendered, env.rendered['cli'])
            env.rendered['cli'] = rendered
            node = UsageExampleNode(cli=example)
            block["nodes"] = [node]
            # Break after seeing the first record created by use.action() since
            # we only need to call use.render() once.
            break


@records_to_nodes.register(ArtifactAPIUsage)
def artifact_api(use, records, block, env):
    for record in records:
        source = record.source
        if source == "init_data":
            data_node = init_data_node(record, env)
            block['nodes'].append(data_node)
        elif source == "init_metadata":
            metadata_node = init_data_node(record, env)
            block['nodes'].append(metadata_node)
        elif source == "action":
            node = block["nodes"][0]
            setup_code = get_data_nodes(env)
            rendered = use.render()
            example = remove_rendered(rendered, env.rendered['art_api'])
            example = setup_code + example
            env.rendered['art_api'] = rendered
            node.artifact_api = example
            # Break after seeing the first record created by use.action() since
            # we only need to call use.render() once.
            break


def init_data_node(record, env):
    name = record.ref
    fname = f"{name}.qza"
    result = env.drivers['exc_use']._get_record(name).result
    type_ = "Artifact" if isinstance(result, qiime2.Artifact) else "Metadata"
    load_statement = f"{name} = {type_}.load('{fname}')"
    node = UsageDataNode(load_statement, name=name)
    return node


def get_data_nodes(env):
    setup_code = []
    for block in env.usage_blocks:
        nodes = block['nodes']
        for node in nodes:
            if isinstance(node, UsageDataNode) and not node.loaded:
                setup_code.append(node.setup)
                node.loaded = True
    return '\n'.join(setup_code) + '\n\n'


def remove_rendered(example, rendered):
    imports = [line for line in rendered.splitlines() if 'import' in line]
    # TODO Don't remove previously rendered variable binding in case the same
    #   name is overwritten
    query = '\n'.join(
        [line for line in rendered.splitlines() if 'import' not in line]
    ).strip()
    example = example.replace(query, '')
    for imp in imports:
        p = re.compile(fr'{imp}\n')
        example = p.sub('', example, count=1)
    p = re.compile('\n\n+')
    example = p.sub('\n\n', example).strip()
    return example
