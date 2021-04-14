import ast
import functools
import operator
import os
from pathlib import Path
from typing import Tuple, Union

from sphinx.util import logging

import qiime2  # noqa: F401
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

from .meta_usage import MetaUsage
from .utils import get_docname
from .validation import BlockValidator

logger = logging.getLogger(__name__)


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
            exec(source)
            new_records = get_new_records(use, processed_records)
            records_to_nodes(use, new_records, block, env)
            update_processed_records(new_records, processed_records)
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
            result = MetaUsage.execution.value._get_record(ref).result
            if isinstance(result, qiime2.metadata.metadata.Metadata):
                metadata_preview = str(result.to_dataframe())
                node.preview = metadata_preview
        except KeyError as e:
            logger.warning(
                f"Factory `{ref}` is not used in any Usage examples: {e}"
            )


def get_new_records(use, processed_records) -> Union[Tuple[ScopeRecord], None]:
    new_records = tuple()
    records = use._get_records()
    new_record_keys = [k for k in records.keys() if k not in processed_records]
    if new_record_keys:
        new_records = operator.itemgetter(*new_record_keys)(records)
        new_records = ((new_records, )
                       if not isinstance(new_records, tuple)
                       else new_records)
    return new_records


def update_processed_records(new_records, processed_records):
    refs = [i.ref for i in new_records]
    processed_records.extend(refs)


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
    root, doc_name = get_docname(node)
    out_dir = Path(env.app.outdir) / doc_name / 'results'
    if not out_dir.exists():
        out_dir.mkdir(parents=True)
    if block["nodes"][0].factory:
        factories_to_nodes(block, env)
    for record in records:
        artifact = record.result
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
            # Break after seeing the first record created by use.action() since
            # we only need to call use.render() once.
            block["nodes"] = [node]
            break


@records_to_nodes.register(ArtifactAPIUsage)
def artifact_api(use, records, block, env):
    for record in records:
        source = record.source
        if source == "init_data":
            data_node = init_data_node(record)
            block['nodes'].append(data_node)
        elif source == "init_metadata":
            metadata_node = init_data_node(record)
            block['nodes'].append(metadata_node)
        elif source == "action":
            # TODO If it's the first ExampleNode, include `import qiime2`
            node = block["nodes"][0]
            setup_code = get_data_nodes(env)
            rendered = use.render()
            example = remove_rendered(rendered, env.rendered['art_api'])
            env.rendered['art_api'] = rendered
            node.artifact_api = setup_code + example
            # Break after seeing the first record created by use.action() since
            # we only need to call use.render() once.
            break


def init_data_node(record):
    name = record.ref
    fname = f"{name}.qza"
    result = MetaUsage.execution.value._get_record(name).result
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
    imports = '\n'.join(
        [line for line in rendered.splitlines() if 'import' in line]
    )
    query = '\n'.join(
        [line for line in rendered.splitlines() if 'import' not in line]
    ).strip()
    example = example.replace(query, '').strip()
    example = example.replace(imports, '').strip()
    example = example.replace('\n\n\n', '\n\n').strip()
    return example
