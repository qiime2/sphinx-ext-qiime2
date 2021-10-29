from docutils import nodes

from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk.usage import Usage, ExecutionUsageVariable
from q2cli.core.usage import CLIUsageFormatter


class SphinxArtifactUsage(ArtifactAPIUsage):
    def render(self, flush=False):
        rendered = super().render(flush)
        return nodes.literal_block(rendered, rendered)


class SphinxCLIUsage(CLIUsageFormatter):
    def render(self, flush=False):
        rendered = super().render(flush)
        return nodes.literal_block(rendered, rendered)


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

    def render(self, flush=False):
        recs = self.recorder
        if flush:
            self.recorder = {}
        rendered = '\n'.join('%s: %s' % (k, str(r)) for k, r in recs.items())
        return nodes.literal_block(rendered, rendered)

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
