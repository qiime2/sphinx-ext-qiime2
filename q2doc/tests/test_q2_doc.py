import os
import pytest

import qiime2
import qiime2.sdk.usage as usage
from docutils import nodes
import itertools
from qiime2.plugins import ArtifactAPIUsage
from q2cli.core.usage import CLIUsage

from q2doc.usage.usage import records_to_nodes


def data_factory():
    return qiime2.Artifact.import_data('MultiplexedSingleEndBarcodeInSequence',
                                       'roots/test-ext-usage/data/forward.fastq.gz')


def metadata_factory():
    return qiime2.Metadata.load('roots/test-ext-usage/data/metadata.tsv')


def example_init_data(use):
    use.init_data('data', data_factory)
    use.init_metadata('metadata', metadata_factory)
    records = use._scope.records.values()
    return records


def test_records_to_nodes_execution():
    use = usage.ExecutionUsage()
    result = records_to_nodes(use, [])
    assert result == []
    records = example_init_data(use)
    result = records_to_nodes(use, records)
    exp = itertools.zip_longest(result, [], fillvalue=nodes.Node)
    assert all(itertools.starmap(isinstance, exp))
    assert len(result) == 4
    assert result


@pytest.mark.parametrize("use", [CLIUsage(), ArtifactAPIUsage()])
def test_records_to_nodes_cli(use):
    result = records_to_nodes(use, [])
    assert result == []
    example_init_data(use)
    records = use._scope.records.values()
    result = records_to_nodes(use, records)
    assert not result


def test_get_new_records():
    pass


@pytest.mark.sphinx(buildername='html', testroot="ext-usage", freshenv=True)
def test_usage_html(app):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    build_result = (app.outdir / 'cutadapt.html').text()
    assert "qiime2.plugins.cutadapt.methods" in build_result
