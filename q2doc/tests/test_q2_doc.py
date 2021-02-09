import pytest


@pytest.mark.sphinx(buildername='text', testroot="ext-usage", freshenv=True)
def test_usage_text(app):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    build_result = (app.outdir / 'cutadapt.txt').text()
    exp = """
   from qiime2.plugins.cutadapt.methods import demux_single

   barcodes = metadata.get_column('barcodes')

   demultiplexed_seqs, untrimmed = demux_single(
       seqs=data,
       barcodes=barcodes,
       error_rate=0,
   )"""
    assert exp in build_result

@pytest.mark.sphinx(buildername='html', testroot="ext-usage", freshenv=True)
def test_usage_html(app):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    build_result = (app.outdir / 'cutadapt.html').text()
    assert "qiime2.plugins.cutadapt.methods" in build_result
