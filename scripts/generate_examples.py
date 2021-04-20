import textwrap
from q2_mystery_stew.plugin_setup import create_plugin


plugin = create_plugin()


with open("/Users/aas/qiime2/sphinx-ext-qiime2/q2doc/tests/roots/test-mystery-stew/examples.rst", "a") as f:
    dnt = ' ' * 3
    f.write(".. usage::\n   from q2_mystery_stew.plugin_setup import create_plugin\n   plugin = create_plugin()\n\n")
    for k, v in plugin.actions.items():
        action = f"action = plugin.actions['{k}']"
        for name in v.examples:
            title = f"{k} {name}"
            prelude = f"{title}\n{'-' * len(title)}\n\n.. usage::\n"
            example = f"example = action.examples['{name}']"
            use = "example(use)"
            lines = textwrap.indent('\n'.join([action, example, use]), '   ')
            f.write('\n'.join([prelude, lines]))
            f.write('\n\n\n')
