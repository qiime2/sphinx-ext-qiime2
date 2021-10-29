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
        contexts = self.state.document.settings.env.app.contexts

        cmd = '\n'.join(self.content)

        for driver_name, ctx in contexts.items():
            exec(cmd, ctx)
            node = ctx['use'].render(flush=True)
            nodes.append(node)

        return nodes


def setup(app):
    app.connect('builder-inited', setup_usage_drivers)
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
