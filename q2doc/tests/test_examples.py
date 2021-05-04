import pathlib
import pytest

from qiime2.sdk import PluginManager
from q2_mystery_stew.plugin_setup import create_plugin


@pytest.mark.sphinx(buildername='html', testroot="cutadapt", freshenv=True)
def test_cutadapt_example(app, file_regression):
    app.build()
    assert app.statuscode == 0
    assert 'q2doc.usage' in app.extensions
    build_result = app.outdir / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")


def mystery_stew_examples():
    plugin = create_plugin()
    pm = PluginManager(add_plugins=False)
    pm.add_plugin(plugin)
    for action in plugin.actions.values():
        for example_name in action.examples:
            yield action, example_name


def mystery_stew_rst(app, action, example_name):
    import pprint
    import textwrap
    from qiime2.sdk.usage import DiagnosticUsage

    indentation = ' ' * 3
    use = DiagnosticUsage()
    action.examples[f'{example_name}'](use)
    get_action = f"action = plugin.actions['{action.id}']"
    title = f"{action.id}__{example_name}"
    path = pathlib.Path(app.srcdir / 'index.rst')

    meta = []
    # TODO Use jinja template?
    for name, record in use._get_records().items():
        meta.append(f'name: {name}\n')
        meta.append(f'record::\n')
        result = pprint.pformat(record.result).replace("\n", "\n    ")
        meta.append(f'    {result}\n\n')

    meta = '\n'.join(sorted(meta))
    with open(path, "w") as f:
        setup = (
            "from qiime2.sdk import PluginManager",
            "pm = PluginManager()",
            "plugin = pm.get_plugin(id='mystery_stew')",
        )
        example = f"example = action.examples['{example_name}']"
        call = "example(use)"
        lines = textwrap.indent('\n'.join([*setup, get_action, example, call]), indentation)
        title = f"{title}\n{'-' * len(title)}\n"
        directive = ".. usage::\n"
        f.write('\n'.join([title, meta, directive, lines]))


def _labeler(val):
    if hasattr(val, 'id'):
        return val.id
    return val


@pytest.mark.parametrize('action,example_name', mystery_stew_examples(), ids=_labeler)
@pytest.mark.sphinx(buildername='singlehtml', testroot='mystery-stew')
def test_mystery_stew_examples(action, example_name, make_app, app_params, file_regression):
    args, kwargs = app_params
    app = make_app(*args, freshenv=True, **kwargs)
    mystery_stew_rst(app, action, example_name)
    app.build()
    assert app.statuscode == 0
    build_result = app.outdir / 'index.html'
    file_regression.check(build_result.read_text(), extension=".html")
