# ----------------------------------------------------------------------------
# Copyright (c) 2020-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import json
import os
import pathlib
import traceback
import pkg_resources

import sphinx
import docutils.parsers.rst.directives
from docutils import nodes
from sphinx.util.fileutil import copy_asset
import sphinx.errors

from qiime2.sdk import PluginManager

from .driver import (
    SphinxExecUsage,
    SphinxArtifactUsage,
    SphinxCLIUsage,
    SphinxGalaxyUsage,
    SphinxRtifactUsage
)


BASE_CASE = object()


INTERFACES = {
    'python3': {
                     'driver':        SphinxArtifactUsage,
                     'label':        'Python 3 API (qiime2)',
                     'is_interface': True,
                     'class_name':   'python3-usage',
                    },
    'R': {
                    'driver':        SphinxRtifactUsage,
                    'label':         'R API (qiime2)',
                    'is_interface':  True,
                    'class_name':    'r-usage',
    },
    'cli':          {
                     'driver':       SphinxCLIUsage,
                     'label':        'Command Line (q2cli)',
                     'is_interface': True,
                     'class_name':   'cli-usage',
                    },
    'galaxy':       {
                     'driver':       SphinxGalaxyUsage,
                     'label':        'Galaxy (q2galaxy)',
                     'is_interface': True,
                     'class_name':   'galaxy-usage',
                    },
    'exc':          {
                     'driver':       SphinxExecUsage,
                     'label':        'Execution Usage (non-rendering)',
                     'is_interface': False,
                     'class_name':   '',
                    },
    'raw':          {
                     'driver':       None,
                     'label':        'View Source (qiime2.sdk)',
                     'is_interface': False,
                     'class_name':   'raw-usage',
                    },
}


def setup_extension(app):
    app.q2_usage = {
        'plugin_manager': PluginManager(),
        'current_doc': BASE_CASE,
        'contexts': {},
        'scope_names': {},
        'default_interfaces': {},
    }


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
    has_content = True

    option_spec = {
        'default-interface':
            docutils.parsers.rst.directives.unchanged_required,
    }

    def run(self):
        nodes_ = self.setup()
        tag = '<span class="usage-selector"></span>'
        nodes_.append(nodes.raw(tag, tag, format='html'))
        return nodes_

    def setup(self):
        env = self._get_env()

        q2_usage = env.app.q2_usage
        docname = env.docname
        nodes_ = []

        # this means usage-selector directive has not been run in this doc,
        # so let's initialize the interface base case
        if docname not in q2_usage['default_interfaces']:
            default_interface = self.options.get(
                'default-interface', INTERFACES['cli']['class_name'])

            valid_interfaces = [x['class_name'] for x in INTERFACES.values()]
            if default_interface not in valid_interfaces:
                raise sphinx.errors.ExtensionError(
                    'Invalid interface: %s' % default_interface)

            interfaces = {}
            classes = []
            for interface in INTERFACES.values():
                if interface['class_name'] != '':
                    interfaces[interface['class_name']] = [
                        interface['label'],
                        interface['is_interface'],
                    ]
                    classes.append('.%s' % interface['class_name'])
            payload = {
                'default': default_interface,
                'available': interfaces,
                'classes': classes,
            }

            tag = '<script id="interfaces" type="application/json">'
            tag += '%s</script>' % json.dumps(payload)

            nodes_.append(nodes.raw(tag, tag, format='html'))

            q2_usage['default_interfaces'][docname] = default_interface

        return nodes_

    def _get_env(self):
        return self.state.document.settings.env


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
            debug_page = env.config.debug_page
            debug_pg_isnt_current_pg = debug_page != env.docname
        else:
            global_no_exec = os.environ.get('Q2DOC_NO_EXEC', False)
            debug_pg_isnt_current_pg = True

        scope_name = env.app.q2_usage['scope_names'][env.docname]

        for driver, ctx in env.app.q2_usage['contexts'][scope_name].items():
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

        nodes_.insert(
            -2,  # bc execution usage should always be _last_
            nodes.literal_block(cmd, cmd, ids=[self._new_id()],
                                classes=['raw-usage']))
        return nodes_

    def setup(self):
        env = self._get_env()

        q2_usage = env.app.q2_usage
        docname = env.docname

        # this means usage-scope directive has not been run in this doc,
        # so let's use the current docname for the scope's name
        if docname not in q2_usage['scope_names']:
            q2_usage['scope_names'][docname] = docname

        scope_name = q2_usage['scope_names'][docname]

        # save output files based on docname always, rather than using
        # the scope's name
        if q2_usage['current_doc'] != docname:
            q2_usage['current_doc'] = docname

            # find somewhere to stick all the result data
            root_build_dir = pathlib.Path(env.app.outdir)
            doc_data_dir = root_build_dir / 'data' / docname
            doc_data_dir.mkdir(parents=True, exist_ok=True)
            q2_usage['data_dir'] = doc_data_dir

        # if scope hasn't been initialized yet, do that now
        if scope_name not in q2_usage['contexts']:
            # these are the locals() for the individual drivers
            scope = dict()
            for k, v in INTERFACES.items():
                if v['driver'] is not None:
                    scope[k] = {'use': v['driver'](env)}
            q2_usage['contexts'][scope_name] = scope

        env.app.q2_usage = q2_usage

    def _get_env(self):
        return self.state.document.settings.env

    def _new_id(self):
        env = self._get_env()
        return 'usage-%d' % (env.new_serialno('usage'),)


class UsageScopeDirective(docutils.parsers.rst.Directive):
    has_content = True

    option_spec = {
        'name': docutils.parsers.rst.directives.unchanged_required,
    }

    def run(self):
        scope_name = self.options['name']
        env = self.state.document.settings.env
        if env.docname in env.app.q2_usage['scope_names']:
            raise sphinx.errors.ExtensionError(
                'cannot redefine a document\'s scope after '
                'usage has been initialized')

        env.app.q2_usage['scope_names'][env.docname] = scope_name
        return []


def setup(app):
    app.connect('builder-inited', setup_extension)
    app.connect('html-page-context', copy_asset_files)

    app.add_directive('usage', UsageDirective)
    app.add_directive('usage-selector', UsageDirectiveInterfaceSelector)
    app.add_directive('usage-scope', UsageScopeDirective)

    return {'version': '0.0.1'}
