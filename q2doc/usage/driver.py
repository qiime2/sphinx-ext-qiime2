from contextlib import redirect_stdout, redirect_stderr
import io
import os
import pathlib
import shutil
import tempfile
import urllib.parse

from docutils import nodes
import docutils.core

from qiime2.plugin import model
from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk.usage import Usage, ExecutionUsageVariable
from q2cli.core.usage import CLIUsage, CLIUsageVariable
from q2galaxy.api import GalaxyRSTInstructionsUsage


AUTO_COLLECT_SIZE = 3


def _build_url(env, fn):
    baseurl = os.environ.get('Q2DOC_HTML_BASEURL', env.config.html_baseurl)
    if baseurl == '':
        raise ValueError('must set `html_baseurl` sphinx config val')
    parts = list(urllib.parse.urlparse(baseurl))
    parts[2] += 'data/%s/%s' % (env.docname, fn)
    url = urllib.parse.urlunparse(parts)
    return url


class SphinxGalaxyUsage(GalaxyRSTInstructionsUsage):
    def __init__(self, sphinx_env):
        super().__init__()
        self.sphinx_env = sphinx_env

    def _to_cli_name(self, var):
        # Build a tmp cli-based variable, for filename templating!
        return CLIUsageVariable(
            var.name, lambda: None, var.var_type, var.use).to_interface_name()

    def _download_file(self, var):
        fn = self._to_cli_name(var)
        url = _build_url(self.sphinx_env, fn)

        rst = f"""
        Using the ``Upload Data`` tool:
         1. On the first tab (**Regular**), press the ``Paste/Fetch data``
            button at the bottom.

            * Set *"Name"* (the first text-field) to: ``{fn}``
            * In the larger text-area copy-and-paste: {url}
            * (*"Type"*, *"Genome"*, and *"Settings"* can be ignored)

         2. Press the ``Start`` button at the bottom.

        """
        self._add_instructions(rst)

    def _download_collection(self, dir_name, path):
        urls = [(fn, _build_url(self.sphinx_env, os.path.join(dir_name, fn)))
                for fn in os.listdir(path)]

        rst = """
        .. code-block:: text

        """
        for fn, url in urls:
            rst += f"""
           {fn}\t{url}"""

        rst += """
        """

        self._add_instructions(rst)

    def init_metadata(self, name, factory):
        var = super().init_metadata(name, factory)

        self._download_file(var)

        return var

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)

        self._download_file(var)

        return var

    def init_format(self, name, factory):
        var = super().init_format(name, factory)

        fmt = var.execute()
        if isinstance(fmt, model.DirectoryFormat):
            data_dir = self.sphinx_env.app.q2_usage['data_dir']
            dir_name = self._to_cli_name(var)
            save_path = os.path.join(data_dir, dir_name)
            fmt.save(save_path)
            self._download_collection(dir_name, save_path)
        else:
            self._download_file(var)

        return var

    def render(self, node_id, flush=False, **kwargs):
        rendered = super().render(flush)
        container_node = nodes.compound(
            raw_source='', ids=[node_id], classes=['galaxy-usage'])
        tree = docutils.core.publish_doctree('\n'.join(rendered))
        container_node.children = tree.children

        return container_node


class SphinxArtifactUsage(ArtifactAPIUsage):
    def __init__(self, sphinx_env):
        super().__init__(action_collection_size=AUTO_COLLECT_SIZE)
        self.sphinx_env = sphinx_env

    def _to_cli_var(self, var):
        # Build a tmp cli-based variable, for filename templating!
        return CLIUsageVariable(var.name, lambda: None, var.var_type, var.use)

    def _download_file(self, var):
        cli_var = self._to_cli_var(var)
        fn = cli_var.to_interface_name()
        url = _build_url(self.sphinx_env, fn)

        self._update_imports(from_='urllib', import_='request')

        lines = [
            'url = %r' % (url,),
            'fn = %r' % (fn,),
            'request.urlretrieve(url, fn)',
        ]

        self._add(lines)

        return cli_var

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)

        self._download_file(var)
        self._update_imports(from_='qiime2', import_='Artifact')
        input_fp = var.to_interface_name()

        lines = [
            '%s = Artifact.load(fn)' % (input_fp,),
            '',
        ]

        self._add(lines)

        return var

    def init_metadata(self, name, factory):
        var = super().init_metadata(name, factory)

        self._download_file(var)
        self._update_imports(from_='qiime2', import_='Metadata')
        input_fp = var.to_interface_name()

        lines = [
            '%s = Metadata.load(fn)' % (input_fp,),
            '',
        ]

        self._add(lines)

        return var

    def init_format(self, name, factory, ext=None):
        var = super().init_format(name, factory, ext=ext)

        # no ext means a dirfmt, which means we have zipped the computed res.
        if ext is None:
            ext = 'zip'

        fn = '%s.%s' % (name, ext)
        tmp_var = self.usage_variable(fn, lambda: None, var.var_type)
        self._download_file(tmp_var)

        if ext == 'zip':
            self._update_imports(import_='zipfile')
            input_fp = var.to_interface_name()

            lines = [
                'with zipfile.ZipFile(fn) as zf:',
                '    zf.extractall(%r)' % (input_fp,)
            ]

            self._add(lines)

        return var

    def render(self, node_id, flush=False, **kwargs):
        rendered = super().render(flush)

        if rendered == '':
            return None

        return nodes.literal_block(rendered, rendered, ids=[node_id],
                                   classes=['artifact-usage'])


class SphinxCLIUsage(CLIUsage):
    def __init__(self, sphinx_env):
        super().__init__(action_collection_size=AUTO_COLLECT_SIZE)
        self.sphinx_env = sphinx_env

    def _download_file(self, var):
        fn = var.to_interface_name()

        url = _build_url(self.sphinx_env, fn)

        self.recorder.append('wget \\')
        self.recorder.append('  -O %r \\' % fn)
        self.recorder.append('  %r' % url)
        self.recorder.append('')

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)
        self._download_file(var)
        return var

    def init_metadata(self, name, factory):
        var = super().init_metadata(name, factory)
        self._download_file(var)
        return var

    def init_format(self, name, factory, ext=None):
        var = super().init_format(name, factory, ext=ext)

        # no ext means a dirfmt, which means we have zipped the computed res.
        if ext is None:
            ext = 'zip'

        fn = '%s.%s' % (name, ext)
        cli_var = self.usage_variable(fn, lambda: None, var.var_type)
        self._download_file(cli_var)

        if ext == 'zip':
            zip_fp = var.to_interface_name()
            out_fp = cli_var.to_interface_name()
            self.recorder.append('unzip -d %s %s' % (zip_fp, out_fp))

        return var

    def render(self, node_id, flush=False, **kwargs):
        rendered = super().render(flush)

        if rendered == '':
            return None

        return nodes.literal_block(rendered, rendered, ids=[node_id],
                                   classes=['cli-usage'])


class SphinxExecUsageVariable(ExecutionUsageVariable, CLIUsageVariable):
    # ExecutionUsageVariable knows how to assert results
    # CLIUsageVariable knows how to build filesystem filenames
    pass


class SphinxExecUsage(Usage):
    def __init__(self, sphinx_env):
        super().__init__()
        self.recorder = {}
        self.sphinx_env = sphinx_env
        self.cli_use = CLIUsage()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.misc_nodes = []

    def usage_variable(self, name, factory, var_type):
        return SphinxExecUsageVariable(name, factory, var_type, self)

    def _add_record(self, variable):
        self.recorder[variable.to_interface_name()] = variable.execute()
        return variable

    def _save_results(self):
        fns = {}
        data_dir = self.sphinx_env.app.q2_usage['data_dir']
        for fn, result in self.recorder.items():
            fp = str(data_dir / fn)
            if isinstance(result, model.DirectoryFormat):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir = pathlib.Path(tmpdir)
                    with redirect_stdout(self.stdout), \
                            redirect_stderr(self.stderr):
                        result.save(tmpdir / 'dirfmt')
                    fp = shutil.make_archive(fp, 'zip', str(result))
            else:
                with redirect_stdout(self.stdout), \
                        redirect_stderr(self.stderr):
                    fp = result.save(fp)
            fp = pathlib.Path(fp)
            fn_w_ext = fp.relative_to(data_dir)
            fns[fn_w_ext] = _build_url(self.sphinx_env, fn_w_ext)
        return fns

    def _build_result_link_node(self, filename, dl_url):
        filename = str(filename)  # in case of pathlib.Path
        spacer_node = nodes.inline(' | ', ' | ')
        dl_node = nodes.inline('download', 'download')
        dl_ref_node = nodes.reference('', '', dl_node, internal=False,
                                      refuri=dl_url)
        filename_node = nodes.literal(filename, filename)
        content = [filename_node, spacer_node, dl_ref_node]

        if filename.endswith('qza') or filename.endswith('qzv'):
            quoted_url = urllib.parse.quote_plus(dl_url)
            view_url = 'https://view.qiime2.org?src=%s' % (quoted_url,)
            view_node = nodes.inline('view', 'view')
            view_ref_node = nodes.reference('', '', view_node, internal=False,
                                            refuri=view_url)
            content = [filename_node, spacer_node, view_ref_node,
                       spacer_node, dl_ref_node]

        # for some reason i can't just put this all into a list_item node,
        # but going from stuff -> paragraph -> list_item seems to work
        para_node = nodes.paragraph('', '', *content)
        item_node = nodes.list_item('', para_node)

        return item_node

    def _get_result_links(self, output_paths):
        content = []
        if output_paths:
            for fn, output_path in output_paths.items():
                node = self._build_result_link_node(fn, output_path)
                content.append(node)
        return content

    def _construct_stdio_node(self, stream_type, content):
        block_content = '# %s\n' % (stream_type,)
        block_content += content
        node = nodes.literal_block(block_content, block_content)
        return node

    def _construct_file_node(self, fns):
        list_item_nodes = self._get_result_links(fns)
        list_node = nodes.bullet_list('', *list_item_nodes)
        return list_node

    def render(self, node_id, flush=False, stdout=None, stderr=None, **kwargs):
        fns = self._save_results()

        files_node = self._construct_file_node(fns)
        container_node = nodes.compound('', files_node, ids=[node_id],
                                        classes=['exec-usage'])

        if stdout:
            content = self.stdout.getvalue()
            if content != '':
                stdout_node = self._construct_stdio_node('stdout', content)
                container_node.append(stdout_node)

        if stderr:
            content = self.stderr.getvalue()
            if content != '':
                stderr_node = self._construct_stdio_node('stderr', content)
                container_node.append(stderr_node)

        for misc_node in self.misc_nodes:
            container_node.append(misc_node)

        if flush:
            self.recorder = {}
            self.stdout.truncate(0)
            self.stdout.seek(0)
            self.stderr.truncate(0)
            self.stderr.seek(0)
            self.misc_nodes = []

        return container_node

    def init_artifact(self, name, factory):
        variable = super().init_artifact(name, factory)
        return self._add_record(variable)

    def init_metadata(self, name, factory):
        variable = super().init_metadata(name, factory)
        return self._add_record(variable)

    def init_format(self, name, factory, ext=None):
        if ext is not None:
            name = '%s.%s' % (name, ext)
        variable = super().init_format(name, factory, ext=ext)

        return self._add_record(variable)

    def import_from_format(self, name, semantic_type, variable,
                           view_type=None):
        variable = super().import_from_format(
            name, semantic_type, variable, view_type=view_type)
        return self._add_record(variable)

    # no merge_metadata or view_as_metadata, we don't need download links
    # for those nodes.

    def get_metadata_column(self, name, column_name, variable):
        return super().get_metadata_column(name, column_name, variable)

    def action(self, action, input_opts, output_opts):
        variables = super().action(action, input_opts, output_opts)

        if len(variables) > AUTO_COLLECT_SIZE:
            plugin_name = CLIUsageVariable.to_cli_name(action.plugin_id)
            action_name = CLIUsageVariable.to_cli_name(action.action_id)
            dir_name = self.cli_use._build_output_dir_name(plugin_name,
                                                           action_name)
            data_dir = self.sphinx_env.app.q2_usage['data_dir']
            output_dir = data_dir / dir_name
            output_dir.mkdir(exist_ok=True)
            self.cli_use._rename_outputs(variables._asdict(), str(output_dir))

        for variable in variables:
            self._add_record(variable)

        return variables

    def peek(self, variable):
        result = variable.execute()

        uuid = result.uuid
        type_ = result.type
        fmt = result.format

        node_elems = []
        for term, defn in [('UUID', uuid), ('Type', type_), ('Format', fmt)]:
            term_node = nodes.strong(text=term+' ')
            defn_node = nodes.literal(text=defn)
            item_node = nodes.list_item('', term_node, defn_node)
            node_elems.append(item_node)
        list_node = nodes.bullet_list('', *node_elems)
        self.misc_nodes.append(list_node)
