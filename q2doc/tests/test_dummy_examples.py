import pytest


@pytest.mark.sphinx(buildername='html', testroot="examples", freshenv=True)
def test_dummy_examples(app, file_regression, monkeypatch):
    with monkeypatch.context() as m:
        m.setenv('QIIMETEST', '1')
        app.build()
    assert app.statuscode == 0
    build_result = app.outdir / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")
