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

DATA = pathlib.Path(__file__).parent / "roots" / "test-q2doc" / "data"


def data_factory():
    return qiime2.Artifact.import_data('MultiplexedSingleEndBarcodeInSequence',
                                       DATA / 'forward.fastq.gz')


def metadata_factory():
    return qiime2.Metadata.load(DATA / 'metadata.tsv')


@pytest.fixture(params=MetaUsage.__members__.values())
def usage_drivers(request):
    use = request.param.value
    yield use


@pytest.fixture
def example_init_data(usage_drivers):
    use = usage_drivers
    use.init_data('data', data_factory)
    use.init_metadata('metadata', metadata_factory)
    yield use


@pytest.mark.parametrize(
    "driver,exp",
    [(usage.ExecutionUsage, 4), (CLIUsage, 0), (ArtifactAPIUsage, 0)]
)
def test_init_data_records_to_nodes(driver, exp):
    use = driver()
    use.init_data('data', data_factory)
    use.init_metadata('metadata', metadata_factory)
    records = get_new_records(use, [])
    result = records_to_nodes(use, records, [])
    exp_nodes = itertools.zip_longest(result, [], fillvalue=nodes.Node)
    assert all(itertools.starmap(isinstance, exp_nodes))
    assert len(result) == exp


def test_records_to_nodes_no_records(usage_drivers):
    use = usage_drivers
    result = records_to_nodes(use, {}, [])
    assert not result


def test_get_new_records(example_init_data):
    use = example_init_data
    result = get_new_records(use, [])
    exp = itertools.zip_longest(result, [], fillvalue=usage.ScopeRecord)
    assert len(result) == 2
    assert all(itertools.starmap(isinstance, exp))
    seen = [i.ref for i in result]
    result = get_new_records(use, processed_records=seen)
    assert result is None


@pytest.mark.sphinx(buildername='dirhtml', testroot="q2doc", freshenv=True,
                    confoverrides={"command_block_no_exec": True})
def test_usage_html(app, file_regression):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    build_result = app.outdir / 'tutorials' / 'cutadapt' / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")


@pytest.mark.sphinx(buildername='html', testroot="q2doc", freshenv=True)
def test_command_block_html(app):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.command_block' in app.extensions
