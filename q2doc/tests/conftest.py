import pathlib
import textwrap

import pytest
from sphinx.testing.path import path

from qiime2.sdk import PluginManager
from q2_mystery_stew.plugin_setup import create_plugin

from qiime2.sdk.usage import DiagnosticUsage

collect_ignore = ['roots']
pytest_plugins = 'sphinx.testing.fixtures'


@pytest.fixture(scope='function')
def rootdir():
    """Sets root folder for sphinx unit tests."""
    return path(__file__).parent.abspath() / 'roots'


def get_mystery_stew_names():
    plugin = create_plugin()
    pm = PluginManager(add_plugins=False)
    pm.add_plugin(plugin)
    for action in list(plugin.actions.values())[:5]:
        for example_name in action.examples:
            yield action, example_name


@pytest.mark.sphinx(buildername='html', testroot='mystery-stew')
@pytest.fixture(scope='function', params=get_mystery_stew_names())
def mystery_stew(request, make_app, app_params):
    import pprint
    indentation = ' ' * 3
    action, example_name = request.param
    args, kwargs = app_params
    app = make_app(*args, freshenv=True, **kwargs)

    use = DiagnosticUsage()
    action.examples[f'{example_name}'](use)
    get_action = f"action = plugin.actions['{action.id}']"
    title = f"{action.id}__{example_name}"
    path = pathlib.Path(app.srcdir / 'index.rst')

    meta = []
    for name, record in use._get_records().items():
        meta.append(f'name: {name}\n')
        meta.append(f'record:\n')
        meta.append(f'{pprint.pformat(record.result)}\n\n')

    meta = '\n'.join(meta)
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


    yield app