import pytest


@pytest.mark.sphinx(buildername='html', testroot="ext-usage", freshenv=True)
def test_usage(app):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    content = (app.outdir / 'cutadapt.html').text()
    assert "qiime cutadapt demux-single" in content
