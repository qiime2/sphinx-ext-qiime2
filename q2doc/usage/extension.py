import os
import pathlib
import pkg_resources

import docutils.parsers.rst.directives
from sphinx.util.fileutil import copy_asset

from qiime2.sdk import PluginManager

from .driver import (
    SphinxExecUsage,
    SphinxArtifactUsage,
    SphinxCLIUsage,
)


def copy_asset_files(app, pagename, templatename, context, doctree):
    base_fp = pkg_resources.resource_filename('q2doc', 'usage')
    asset_path = pathlib.Path(base_fp) / 'assets'

    for path in asset_path.glob('*.js'):
        copy_asset(str(path), os.path.join(app.outdir, '_static'))
        app.add_js_file(str(path.name))

    for path in asset_path.glob('*.css'):
        copy_asset(str(path), os.path.join(app.outdir, '_static'))
        app.add_css_file(str(path.name))


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
            use = ctx['use']
            use.sphinx_env = env
            exec(cmd, ctx)
            node_id = self._new_id()
            node = ctx['use'].render(node_id, self.state, flush=True)
            if node is not None:
                nodes.append(node)

        return nodes

    def _get_env(self):
        return self.state.document.settings.env

    def _new_id(self):
        env = self._get_env()
        return 'usage-%d' % (env.new_serialno('usage'),)

def setup(app):
    app.connect('builder-inited', setup_usage_drivers)
    app.connect('html-page-context', copy_asset_files)
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
