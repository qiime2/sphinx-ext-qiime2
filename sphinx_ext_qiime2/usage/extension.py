import docutils.parsers.rst.directives

from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import PluginManager
from qiime2.sdk.usage import Usage, UsageVariable
from q2cli.core.usage import CLIUsageFormatter


class SphinxExecUsageVariable(UsageVariable):
    def assert_has_line_matching(self, path, expression):
        data = self.value

        hits = sorted(data._archiver.data_dir.glob(path))
        if len(hits) != 1:
            raise ValueError('Value provided for path (%s) did not produce '
                             'exactly one hit: %s' % (path, hits))

        target = hits[0].read_text()
        match = re.search(expression, target, flags=re.MULTILINE)
        if match is None:
            raise AssertionError('Expression %r not found in %s.' %
                                 (expression, path))

    def assert_output_type(self, semantic_type):
        data = self.value

        if str(data.type) != str(semantic_type):
            raise AssertionError("Output %r has type %s, which does not match"
                                 " expected output type of %s"
                                 % (self.name, data.type, semantic_type))


class SphinxExecUsage(Usage):
    def __init__(self, asynchronous=False):
        super().__init__(asynchronous)
        self.recorder = {}

    def variable_factory(self, name, factory, var_type):
        return SphinxExecUsageVariable(
            name,
            factory,
            var_type,
            self,
        )

    def _add_record(self, variable):
        variable.execute()
        self.recorder[variable.name] = variable.value
        return variable

    def render(self, flush=True):
        records = self.recorder
        if flush:
            self.recorder = {}
        return records

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


def setup_usage_drivers(app):
    PluginManager()
    app.contexts = {
        'artifact_api': {'use': ArtifactAPIUsage()},
        'cli': {'use': CLIUsageFormatter()},
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
            rendered = ctx['use'].render(flush=True)
            if isinstance(rendered, dict):
                rendered = '\n'.join('%s: %s' % (k, str(r)) for k, r in rendered.items())
                nodes.append(docutils.nodes.literal_block(rendered, rendered))
            else:
                nodes.append(docutils.nodes.literal_block(rendered, rendered))

        return nodes


def setup(app):
    app.connect('builder-inited', setup_usage_drivers)
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
