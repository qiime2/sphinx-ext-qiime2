import os
import pathlib
import traceback
import pkg_resources

import sphinx
import docutils.parsers.rst.directives
from docutils import nodes
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


class UsageDirectiveInterfaceSelector(docutils.parsers.rst.Directive):
    has_content = False

    def run(self):
        tag = '<span class="usage-selector"></span>'
        return [nodes.raw(tag, tag, format='html')]


class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    option_spec = {
        'no-exec': docutils.parsers.rst.directives.flag,
        'stdout': docutils.parsers.rst.directives.flag,
        'stderr': docutils.parsers.rst.directives.flag,
    }

    def run(self):
        if not self.content:
            raise sphinx.errors.ExtensionError(
                'Content required for the %s directive.' % self.name)

        opts = self.options
        no_exec = 'no_exec' in opts
        stdout = 'stdout' in opts
        stderr = 'stderr' in opts

        self.setup()

        nodes_ = []
        cmd = '\n'.join(self.content)

        env = self._get_env()
        # this is to support this extension in the user docs, and also in
        # a standalone setting, such as on the Library
        if hasattr(env.config, 'command_block_no_exec'):
            global_no_exec = env.config.command_block_no_exec
        else:
            global_no_exec = False

        # this is to support this extension in the user docs, and also in
        # a standalone setting, such as on the Library
        if hasattr(env.config, 'debug_page'):
            debug_page = env.config.debug_page
            debug_pg_isnt_current_pg = debug_page != env.docname
        else:
            debug_pg_isnt_current_pg = False

        for driver, ctx in env.app.contexts.items():
            if driver == 'exc':
                if no_exec or (global_no_exec and debug_pg_isnt_current_pg):
                    continue
            try:
                exec(cmd, ctx)
            except Exception as e:
                spacer = '=' * 79
                error = '\n'.join(traceback.format_exception_only(type(e), e))
                error = error.strip()
                raise ValueError("There was a problem in the %r usage driver,"
                                 " when executing this example:"
                                 "\n\n%s\n%s\n%s\n%s"
                                 % (driver, error, spacer, cmd, spacer)) from e

            node_id = self._new_id()
            node = ctx['use'].render(
                node_id,
                flush=True,
                stdout=stdout,
                stderr=stderr,
            )
            if node is not None:
                nodes_.append(node)


        nodes_.append(
            nodes.literal_block(cmd, cmd, ids=[self._new_id()],
                                classes=['raw-usage']))
        return nodes_

    def setup(self):
        env = self._get_env()

        env.app.q2_plugin_manager = PluginManager()

        if not hasattr(env.app, 'q2_current_doc'):
            env.app.q2_current_doc = 'base case'

        if env.app.q2_current_doc != env.docname:
            env.app.q2_current_doc = env.docname

            # find somewhere to stick all the result data
            root_build_dir = pathlib.Path(env.app.outdir)
            doc_data_dir = root_build_dir / 'data' / env.docname
            doc_data_dir.mkdir(parents=True, exist_ok=True)
            env.app.q2_data_dir = doc_data_dir

            # these are the locals() for the individual drivers
            env.app.contexts = {
                # don't forget to update usage.js when changing this list
                'artifact_api': {'use': SphinxArtifactUsage(env)},
                'cli':          {'use': SphinxCLIUsage(env)},
                'exc':          {'use': SphinxExecUsage(env)},
            }

    def _get_env(self):
        return self.state.document.settings.env

    def _new_id(self):
        env = self._get_env()
        return 'usage-%d' % (env.new_serialno('usage'),)


def setup(app):
    app.connect('html-page-context', copy_asset_files)
    app.add_directive('usage', UsageDirective)
    app.add_directive('usage-selector', UsageDirectiveInterfaceSelector)

    return {'version': '0.0.1'}
