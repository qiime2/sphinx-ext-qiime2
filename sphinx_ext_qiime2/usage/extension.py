from io import StringIO
from contextlib import redirect_stdout

import docutils.parsers.rst.directives


from qiime2.plugins import ArtifactAPIUsage


class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        use = ArtifactAPIUsage()

        cmd = '\n'.join(self.content)

        cmd_node = docutils.nodes.literal_block(cmd, cmd)

        buf = StringIO()
        with redirect_stdout(buf):
            locals()['use'] = use
            # JUST DO IT
            exec(cmd, globals(), locals())
        stdout = buf.getvalue()

        stdout_node = docutils.nodes.literal_block(stdout, stdout)

        rendered = use.render()

        rendered_usage_node = docutils.nodes.literal_block(rendered, rendered)

        return [cmd_node, stdout_node, rendered_usage_node]


def setup(app):
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
