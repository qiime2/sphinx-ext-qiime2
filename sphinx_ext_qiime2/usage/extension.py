import docutils.parsers.rst.directives

from qiime2.sdk import PluginManager

from .driver import (
    SphinxExecUsage,
    SphinxArtifactUsage,
    SphinxCLIUsage,
)


def setup_usage_drivers(app):
    PluginManager()
    app.contexts = {
        'artifact_api': {'use': SphinxArtifactUsage()},
        'cli': {'use': SphinxCLIUsage()},
        'exc': {'use': SphinxExecUsage()},
    }


class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        nodes = []
        env = self._get_env()

        cmd = '\n'.join(self.content)

        for driver_name, ctx in env.app.contexts.items():
            exec(cmd, ctx)
            node_id = self._new_id()
            node = ctx['use'].render(node_id, flush=True)
            nodes.append(node)

        return nodes

    def _get_env(self):
        return self.state.document.settings.env

    def _new_id(self):
        env = self._get_env()
        return 'usage-%d' % (env.new_serialno('usage'),)

def setup(app):
    app.connect('builder-inited', setup_usage_drivers)
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
