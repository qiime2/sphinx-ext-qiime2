import docutils.parsers.rst.directives

from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import PluginManager
from qiime2.sdk.usage import ExecutionUsage
from q2cli.core.usage import CLIUsageFormatter


def render_artifact_api(use):
    rendered =  use.render()
    use.recorder = []
    return '# artifact api:\n\n%s' % rendered


def render_cli(use):
    rendered = '\n'.join(use.lines)
    use.lines = []
    return '# q2cli:\n\n%s' % rendered


def render_exc(use):
    rendered = '\n'.join(use.records.keys())
    use.records = {}
    return 'executed:\n\n%s' % rendered


render = {
    'artifact_api': render_artifact_api,
    'cli': render_cli,
    'exc': render_exc,
}


def setup_usage_drivers(app):
    PluginManager()
    app.contexts = {
        'artifact_api': {'use': ArtifactAPIUsage()},
        'cli': {'use': CLIUsageFormatter()},
        'exc': {'use': ExecutionUsage()},
    }


class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        nodes = []
        contexts = self.state.document.settings.env.app.contexts

        cmd = '\n'.join(self.content)

        for driver_name, ctx in contexts.items():
            exec(cmd, ctx)
            rendered = render[driver_name](ctx['use'])
            rendered_usage_node = docutils.nodes.literal_block(rendered, rendered)
            nodes.append(rendered_usage_node)

        return nodes


def setup(app):
    app.connect('builder-inited', setup_usage_drivers)
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
