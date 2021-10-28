from io import StringIO
from contextlib import redirect_stdout

import docutils.parsers.rst.directives


from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import PluginManager
from qiime2.sdk.usage import ExecutionUsage


class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        PluginManager()

        uses = ArtifactAPIUsage()
        exc = ExecutionUsage()

        cmd = '\n'.join(self.content)

        buf = StringIO()
        with redirect_stdout(buf):
            exec(cmd, dict(), {'use': use})
        exec(cmd, {'use': exc})

        stdout = buf.getvalue()

        rendered = use.render()
        rendered_usage_node = docutils.nodes.literal_block(rendered, rendered)

        outputs = '\n'.join(exc.records.keys())
        outputs_node = docutils.nodes.literal_block(outputs, outputs)

        # BREAK IN CASE OF EMERGENCY
        # cmd_node = docutils.nodes.literal_block(cmd, cmd)
        # stdout_node = docutils.nodes.literal_block(stdout, stdout)
        # return [cmd_node, stdout_node, rendered_usage_node]
        return [rendered_usage_node, outputs_node]


def setup(app):
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
