import docutils.parsers.rst.directives

from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import PluginManager
from qiime2.sdk.usage import ExecutionUsage
from q2cli.core.usage import CLIUsageFormatter


def render_artifact_api(use):
    rendered =  use.render()
    use.recorder = []
    return rendered


def render_cli(use):
    rendered = '\n'.join(use.lines)
    use.lines = []
    return rendered


render = {
    'artifact_api': render_artifact_api,
    'cli': render_cli,
}


def setup_usage_drivers(app):
    PluginManager()
    app.exc = {'use': ExecutionUsage()}
    app.contexts = {
        'artifact_api': {'use': ArtifactAPIUsage()},
        'cli': {'use': CLIUsageFormatter()},
    }


class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        nodes = []
        env = self.state.document.settings.env
        contexts = env.app.contexts
        exc = env.app.exc

        cmd = '\n'.join(self.content)

        for driver_name, ctx in contexts.items():
            exec(cmd, ctx)
            rendered = render[driver_name](ctx['use'])
            rendered_usage_node = docutils.nodes.literal_block(rendered, rendered)
            nodes.append(rendered_usage_node)

        exec(cmd, exc)
        outputs = '\n'.join(exc['use'].records.keys())
        outputs_node = docutils.nodes.literal_block(outputs, outputs)
        nodes.append(outputs_node)

        return nodes


def setup(app):
    app.connect('builder-inited', setup_usage_drivers)
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
