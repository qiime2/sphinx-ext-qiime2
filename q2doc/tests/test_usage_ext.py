import itertools
import os
import pathlib

import pytest
import qiime2
import qiime2.sdk.usage as usage
from docutils import nodes
from q2cli.core.usage import CLIUsage
from q2doc.usage.usage import MetaUsage, get_new_records, records_to_nodes
from qiime2.plugins import ArtifactAPIUsage

DATA = pathlib.Path(__file__).parent / "roots" / "test-ext-usage" / "data"

def data_factory():
    return qiime2.Artifact.import_data('MultiplexedSingleEndBarcodeInSequence',
                                       DATA / 'forward.fastq.gz')


def metadata_factory():
    return qiime2.Metadata.load(DATA / 'metadata.tsv')


def example_init_data(use):
    use.init_data('data', data_factory)
    use.init_metadata('metadata', metadata_factory)


@pytest.fixture(params=MetaUsage.__members__.values())
def driver(request):
    use = request.param.value
    yield use


def test_records_to_nodes_execution():
    use = usage.ExecutionUsage()
    example_init_data(use)
    records = get_new_records(use, [])
    result = records_to_nodes(use, records, [])
    exp = itertools.zip_longest(result, [], fillvalue=nodes.Node)
    assert all(itertools.starmap(isinstance, exp))
    assert len(result) == 4


def test_records_to_nodes_no_records(driver):
    use = driver
    result = records_to_nodes(use, {}, [])
    assert not result


def test_get_new_records(driver):
    use = driver
    result = get_new_records(use, [])
    assert result is None
    example_init_data(use)
    result = get_new_records(use, [])
    exp = itertools.zip_longest(result, [], fillvalue=usage.ScopeRecord)
    assert len(result) == 2
    assert all(itertools.starmap(isinstance, exp))
    seen = [i.ref for i in result]
    result = get_new_records(use, processed_records=seen)
    assert result is None


@pytest.mark.sphinx(buildername='html', testroot="ext-usage", freshenv=True)
def test_usage_html(app, file_regression):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    build_result = (app.outdir / 'cutadapt.html').text()
    file_regression.check(build_result, extension=".html")


@pytest.mark.sphinx(buildername='html', testroot="ext-command-block", freshenv=True)
def test_command_block_html(app):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.command_block' in app.extensions
