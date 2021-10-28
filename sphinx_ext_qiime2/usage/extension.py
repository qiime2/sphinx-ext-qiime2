import docutils.parsers.rst.directives

from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import PluginManager
from qiime2.sdk.usage import ExecutionUsage
from q2cli.core.usage import CLIUsageFormatter


def render_artifact_api(use):
    return use.render()

def render_cli(use):
    return '\n'.join(use.lines)


render = {
    'artifact_api': render_artifact_api,
    'cli': render_cli,
}

class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        nodes = []
        PluginManager()

        exc = ExecutionUsage()
        uses = {
            'artifact_api': ArtifactAPIUsage(),
            'cli': CLIUsageFormatter(),
        }

        cmd = '\n'.join(self.content)

        for driver_name, use in uses.items():
            exec(cmd, dict(), {'use': use})
            rendered = render[driver_name](use)
            rendered_usage_node = docutils.nodes.literal_block(rendered, rendered)
            nodes.append(rendered_usage_node)

        exec(cmd, {'use': exc})
        outputs = '\n'.join(exc.records.keys())
        outputs_node = docutils.nodes.literal_block(outputs, outputs)
        nodes.append(outputs_node)

        return nodes


def setup(app):
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
