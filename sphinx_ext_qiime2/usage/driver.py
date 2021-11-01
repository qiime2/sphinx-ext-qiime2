import pathlib

from docutils import nodes, statemachine

import qiime2
from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk.usage import Usage, ExecutionUsageVariable
from q2cli.core.usage import CLIUsageFormatter


class SphinxArtifactUsage(ArtifactAPIUsage):
    def render(self, node_id, env, state, flush=False):
        rendered = super().render(flush)
        node_type = nodes.target if rendered == '' else nodes.literal_block
        return node_type(
            rendered, rendered, ids=[node_id], classes=['artifact-usage'])


class SphinxCLIUsage(CLIUsageFormatter):
    def render(self, node_id, env, state, flush=False):
        rendered = super().render(flush)
        if rendered == '':
            return None
        return nodes.literal_block(
            rendered, rendered, ids=[node_id], classes=['cli-usage'])


class SphinxExecUsage(Usage):
    def __init__(self, asynchronous=False):
        super().__init__(asynchronous)
        self.recorder = {}

    def variable_factory(self, name, factory, var_type):
        # ExecutionUsageVariable knows how to assert results
        return ExecutionUsageVariable(name, factory, var_type, self)

    def _add_record(self, variable):
        variable.execute()
        self.recorder[variable.name] = variable.value
        return variable

    def _setup_data_dir(self, env):
        doc_tree_dir = pathlib.Path(env.doctreedir)
        root_build_dir = doc_tree_dir.parent / env.app.builder.name
        doc_data_dir = root_build_dir / 'data' / env.docname
        doc_data_dir.mkdir(parents=True, exist_ok=True)
        return doc_data_dir

    def _save_results(self, env):
        fns = {}
        doc_data_dir = self._setup_data_dir(env)
        for fn, result in self.recorder.items():
            fp = result.save(str(doc_data_dir / fn))
            fn_w_ext = pathlib.Path(fp).name
            fns[fn_w_ext] = pathlib.Path('data') / env.docname / fn_w_ext
        return fns

    def _get_result_links(self, output_paths):
        content = []
        if output_paths:
            for fn, output_path in output_paths.items():
                content.append('* `%s <%s>`__' % (fn, output_path))
                content.append('')
        return content

    def _construct_node(self, fns, node_id, env, state):
        content = self._get_result_links(fns)
        content = statemachine.ViewList(content, env.docname)
        node = nodes.bullet_list(ids=[node_id], classes=['exec-usage'])
        state.nested_parse(content, 0, node)
        return node

    def render(self, node_id, env, state, flush=False):
        fns = self._save_results(env)

        if flush:
            self.recorder = {}

        node = self._construct_node(fns, node_id, env, state)
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
