import itertools
import pathlib
from unittest.mock import Mock

import pytest
from docutils import nodes

import qiime2
import qiime2.sdk.usage as usage
from q2cli.core.usage import CLIUsage
from q2doc.usage.usage import get_new_records, records_to_nodes
from q2doc.usage.meta_usage import MetaUsage
from qiime2.plugins import ArtifactAPIUsage

DATA = pathlib.Path(__file__).parent / "roots" / "test-q2doc" / "data"


@pytest.fixture(params=MetaUsage.__members__.values())
def usage_drivers(request):
    use = request.param.value
    yield use


@pytest.fixture
def drivers_with_initialized_data(usage_drivers):
    use = usage_drivers
    init_data(use)
    yield use


def data_factory():
    return qiime2.Artifact.import_data(
        'MultiplexedSingleEndBarcodeInSequence',
        DATA / 'forward.fastq.gz')


def metadata_factory():
    return qiime2.Metadata.load(DATA / 'metadata.tsv')


def init_data(use):
    data = use.init_data('data', data_factory)
    metadata = use.init_metadata('metadata', metadata_factory)
    use.init_data('data', data_factory)
    use.init_metadata('metadata', metadata_factory)
    return use, data, metadata


def cutadapt_example(use, data, metadata):
    barcodes_col = use.get_metadata_column('barcodes', metadata)
    use.action(
        usage.UsageAction(
            plugin_id='cutadapt',
            action_id='demux_single',
        ),
        usage.UsageInputs(
            seqs=data,
            error_rate=0,
            barcodes=barcodes_col,
        ),
        usage.UsageOutputNames(
            per_sample_sequences='demultiplexed_seqs',
            untrimmed_sequences='untrimmed',
        )
    )


def test_records_to_nodes_no_records(usage_drivers):
    use = usage_drivers
    result = records_to_nodes(use, {}, )
    assert not result


def test_records_to_nodes_execution_usage():
    use = usage.ExecutionUsage()
    use, data, metadata = init_data(use)
    records = get_new_records(use, [])
    result = records_to_nodes(use, records, )

    exp_nodes = itertools.zip_longest(result, [], fillvalue=nodes.Node)
    assert all(itertools.starmap(isinstance, exp_nodes))
    assert len(result) == 4

    cutadapt_example(use, data, metadata)
    records = get_new_records(use, [])
    result = records_to_nodes(use, records, )


def test_records_to_nodes_cli_usage():
    use = CLIUsage()
    use, data, metadata = init_data(use)
    records = get_new_records(use, [])
    result = records_to_nodes(use, records, )

    exp_nodes = itertools.zip_longest(result, [], fillvalue=nodes.Node)
    assert all(itertools.starmap(isinstance, exp_nodes))
    assert len(result) == 0

    cutadapt_example(use, data, metadata)
    records = get_new_records(use, [])
    result = records_to_nodes(use, records, )


def test_records_to_nodes_artifact_api_usage():
    use = ArtifactAPIUsage()
    use, data, metadata = init_data(use)

    records = get_new_records(use, [])
    result = records_to_nodes(use, records, )

    exp_nodes = itertools.zip_longest(result, [], fillvalue=nodes.Node)
    assert all(itertools.starmap(isinstance, exp_nodes))
    assert len(result) == 0
    cutadapt_example(use, data, metadata)

    records = get_new_records(use, [])
    result = records_to_nodes(use, records, )


def test_get_new_records(drivers_with_initialized_data):
    use = drivers_with_initialized_data
    result = get_new_records(use, [])
    exp = itertools.zip_longest(result, [], fillvalue=usage.ScopeRecord)
    assert len(result) == 2
    assert all(itertools.starmap(isinstance, exp))
    seen = [i.ref for i in result]
    result = get_new_records(use, processed_records=seen)
    assert result == tuple()


@pytest.mark.sphinx(buildername='dirhtml', testroot="cutadapt", freshenv=True)
def test_cutadapt_html(app, file_regression):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    build_result = app.outdir / 'cutadapt' / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")


@pytest.mark.sphinx(buildername='singlehtml', testroot="examples", freshenv=True)
def test_examples_html(app, file_regression):
    app.build()
    assert app.statuscode == 0
    build_result = app.outdir / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")


@pytest.mark.sphinx(buildername='singlehtml', testroot="mystery-stew", freshenv=True)
def test_mystery_stew(app, file_regression):
    from q2_mystery_stew.plugin_setup import create_plugin
    from qiime2.sdk import PluginManager

    plugin = create_plugin()
    pm = PluginManager(add_plugins=False)
    pm.add_plugin(plugin)

    app.build()
    assert app.statuscode == 0
    build_result = app.outdir / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")


def test_mystery_stew_examples(mystery_stew, file_regression):
    app = mystery_stew
    app.build()
    assert app.statuscode == 0
    build_result = app.outdir / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")
