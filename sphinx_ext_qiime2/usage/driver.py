import pathlib
import urllib.parse

from docutils import nodes, statemachine

from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk.usage import Usage, ExecutionUsageVariable
from q2cli.core.usage import CLIUsageFormatter, CLIUsageVariable


def _build_url(env, fn):
    baseurl = env.config.html_baseurl

    if baseurl == '':
        raise ValueError('must set `baseurl` sphinx config val')

    parts = list(urllib.parse.urlparse(baseurl))
    parts[2] = 'data/%s/%s' % (env.docname, fn)
    url = urllib.parse.urlunparse(parts)
    return url


class SphinxArtifactUsage(ArtifactAPIUsage):
    def _build_request(self, var):
        # Build a tmp cli-based variable, for filename templating!
        cli_var = CLIUsageVariable(var.name, lambda: None, var.var_type, var.use)
        fn = cli_var.to_interface_name()
        url = _build_url(self.sphinx_env, fn)

        imps = [('urllib.request', 'urlretrieve'), ('qiime2.sdk', 'Result')]
        for imp in imps:
            if imp not in self.global_imports:
                self.local_imports.add(imp)
                self.global_imports.add(imp)

        self.recorder.append('urlretrieve(%r, %r)' % (url, fn))
        self.recorder.append('%s = Result.load(%r)\n' % (var.name, fn))

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)
        self._build_request(var)
        return var

    def init_metadata(self, name, factory):
        var = super().init_artifact(name, factory)
        self._build_request(var)
        return var

    def render(self, node_id, state, flush=False):
        rendered = super().render(flush)
        return nodes.literal_block(
            rendered, rendered, ids=[node_id], classes=['artifact-usage'])


class SphinxCLIUsage(CLIUsageFormatter):
    def _build_request(self, var):
        fn = var.to_interface_name()
        url = _build_url(self.sphinx_env, fn)

        self.recorder.append('wget -O %s %s' % (fn, url))

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)
        self._build_request(var)
        return var

    def init_metadata(self, name, factory):
        var = super().init_metadata(name, factory)
        self._build_request(var)
        return var

    def render(self, node_id, state, flush=False):
        rendered = super().render(flush)
        return nodes.literal_block(
            rendered, rendered, ids=[node_id], classes=['cli-usage'])


class SphinxExecUsageVariable(ExecutionUsageVariable, CLIUsageVariable):
    # ExecutionUsageVariable knows how to assert results
    # CLIUsageVariable knows how to build filesystem filenames
    pass


class SphinxExecUsage(Usage):
    def __init__(self):
        super().__init__()
        self.recorder = {}

    def variable_factory(self, name, factory, var_type):
        return SphinxExecUsageVariable(name, factory, var_type, self)

    def _add_record(self, variable):
        variable.execute()
        self.recorder[variable.to_interface_name()] = variable.value
        return variable

    def _setup_data_dir(self):
        doc_tree_dir = pathlib.Path(self.sphinx_env.doctreedir)
        root_build_dir = doc_tree_dir.parent / self.sphinx_env.app.builder.name
        doc_data_dir = root_build_dir / 'data' / self.sphinx_env.docname
        doc_data_dir.mkdir(parents=True, exist_ok=True)
        return doc_data_dir

    def _save_results(self):
        fns = {}
        doc_data_dir = self._setup_data_dir()
        for fn, result in self.recorder.items():
            fp = result.save(str(doc_data_dir / fn))
            fn_w_ext = pathlib.Path(fp).name
            fns[fn_w_ext] = _build_url(self.sphinx_env, fn_w_ext)
        return fns

    def _get_result_links(self, output_paths):
        content = []
        if output_paths:
            for fn, output_path in output_paths.items():
                content.append('* `%s <%s>`__' % (fn, output_path))
                content.append('')
        return content

    def _construct_node(self, fns, node_id, state):
        content = self._get_result_links(fns)
        content = statemachine.ViewList(content, self.sphinx_env.docname)
        node = nodes.bullet_list(ids=[node_id], classes=['exec-usage'])
        state.nested_parse(content, 0, node)
        return node

    def render(self, node_id, state, flush=False):
        fns = self._save_results()

        if flush:
            self.recorder = {}

        node = self._construct_node(fns, node_id, state)
        return node

    def init_artifact(self, name, factory):
        variable = super().init_artifact(name, factory)
        return self._add_record(variable)

    def init_metadata(self, name, factory):
        variable = super().init_metadata(name, factory)
        return self._add_record(variable)

    def merge_metadata(self, name, *variables):
        variable = super().merge_metadata(name, *variables)
        return self._add_record(variable)

    def get_metadata_column(self, name, column_name, variable):
        variable = super().get_metadata_column(name, column_name, variable)
        return self._add_record(variable)

    def action(self, action, input_opts, output_opts):
        variables = super().action(action, input_opts, output_opts)
        [self._add_record(v) for v in variables]
        return variables
