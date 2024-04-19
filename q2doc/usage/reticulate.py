from dataclasses import dataclass
import re

from qiime2.sdk import usage
from qiime2.plugins import _canonical_module


class RtifactAPIUsageVariable(usage.UsageVariable):
    """A specialized implementation for :class:`ArtifactAPIUsage`."""
    # this lets us repr all inputs (including parameters) and have
    # them template out in a consistent manner. without this we would wind
    # up with `foo('my_artifact')` rather than `foo(my_artifact)`.
    class repr_raw_variable_name:
        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return self.value

    def to_interface_name(self):
        if self.var_type == 'format':
            return self.name

        parts = {
            'artifact': [self.name],
            'artifact_collection': [self.name, 'artifact_collection'],
            'visualization': [self.name, 'viz'],
            'visualization_collection': [self.name, 'viz_collection'],
            'metadata': [self.name, 'md'],
            'column': [self.name, 'mdc'],
            # No format here - it shouldn't be possible to make it this far
        }[self.var_type]
        var_name = '_'.join(parts)
        # ensure var_name is a valid python identifier
        var_name = re.sub(r'\W|^(?=\d)', '_', var_name)
        return self.repr_raw_variable_name(var_name)

    def assert_has_line_matching(self, path, expression):
        if not self.use.enable_assertions:
            return

        self.use._update_imports(import_='re')
        name = self.to_interface_name()
        expr = expression

        lines = [
            'hits <- sort(%r$_archiver$data_dir$glob(%r))' % (name, path),
            'if ( length(hits) != 1 ) {',
            self.use.INDENT + 'stop("No such path in artifact.")',
            '}',
            'target <- hits[0]$read_text()',
            'match <- re$search(%r, target, flags=re.MULTILINE)' % (expr,),
            'if ( is.null(match) ) {',
            self.use.INDENT + 'stop("No such matching line.")',
            '}',
        ]

        self.use._add(lines)

    def assert_output_type(self, semantic_type, key=None):
        if not self.use.enable_assertions:
            return

        name = self.to_interface_name()

        if key:
            name = "%s[%s]" % (name, key)

        lines = [
            'if ( bulitins$str(%r$type) != %r ) {' % (
                name, str(semantic_type)
            ),
            self.use.INDENT + 'stop("Output is not of the expected type.")',
            '}',
        ]

        self.use._add(lines)


class RtifactAPIUsage(usage.Usage):
    INDENT = ' ' * 4

    @dataclass(frozen=True)
    class ImporterRecord:
        import_: str
        from_: str = None
        as_: str = None

        def render(self):
            if self.as_:
                template = f'{self.as_} <- import("'
            else:
                template = f'{self.import_} <- import("'

            if self.from_:
                template += f'{self.from_}")${self.import_}'
            else:
                template += f'{self.import_}")'

            return template

    def __init__(self, enable_assertions: bool = False):
        """Constructor for ArtifactAPIUsage

        Warning
        -------
        For SDK use only. Do not use in a written usage example.

        Parameters
        ----------
        enable_assertions : bool
            Whether :class:`qiime2.sdk.usage.UsageVariable` assertions should
            be rendered. Note that these are not executed, rather code that
            would assert is templated by :meth:`render`.
        """
        super().__init__()
        self.enable_assertions = enable_assertions
        self._reset_state(reset_global_imports=True)
        self.reticulate_imported = False

    def _reset_state(self, reset_global_imports=False):
        self.local_imports = set()
        self.recorder = []
        self.init_data_refs = dict()
        if reset_global_imports:
            self.global_imports = set()

    def _add(self, lines):
        self.recorder.extend(lines)

    def usage_variable(self, name, factory, var_type):
        return RtifactAPIUsageVariable(name, factory, var_type, self)

    # TODO: template `use_condaenv`
    def render(self, flush: bool = False) -> str:
        """Return a newline-seperated string of Artifact API python code.

        Warning
        -------
        For SDK use only. Do not use in a written usage example.

        Parameters
        ----------
        flush : bool
            Whether to 'flush' the current code. Importantly, this will clear
            the top-line imports for future invocations.
        """
        sorted_imps = sorted(self.local_imports)
        if sorted_imps:
            sorted_imps = sorted_imps + ['']

        render = sorted_imps + self.recorder

        if not self.reticulate_imported:
            render = ['library(reticulate)', ''] + render
            self.reticulate_imported = True

        rendered = '\n'.join(render)

        if flush:
            self._reset_state()

        return rendered

    def init_artifact(self, name, factory):
        variable = super().init_artifact(name, factory)

        var_name = str(variable.to_interface_name())
        self.init_data_refs[var_name] = variable

        return variable

    def init_metadata(self, name, factory):
        variable = super().init_metadata(name, factory)

        var_name = str(variable.to_interface_name())
        self.init_data_refs[var_name] = variable

        return variable

    def init_artifact_collection(self, name, factory):
        variable = super().init_artifact_collection(name, factory)

        var_name = str(variable.to_interface_name())
        self.init_data_refs[var_name] = variable

        return variable

    def construct_artifact_collection(self, name, members):
        variable = super().construct_artifact_collection(name, members)

        var_name = variable.to_interface_name()

        lines = [f'{var_name} = ResultCollection(dict(']
        for key, member in members.items():
            lines.append(self.INDENT + f"'{key}' = {member.name},")

        lines[-1] = lines[-1].rstrip(',')
        lines.append('))')

        self._update_imports(from_='qiime2', import_='ResultCollection')
        self._add(lines)

        return variable

    def get_artifact_collection_member(self, name, variable, key):
        accessed_variable = super().get_artifact_collection_member(
            name, variable, key
        )

        lines = [
            f"{name} <- {variable.to_interface_name()}['{key}']"
        ]
        self._add(lines)

        return accessed_variable

    def init_format(self, name, factory, ext=None):
        if ext is not None:
            name = '%s.%s' % (name, ext.lstrip('.'))

        variable = super().init_format(name, factory, ext=ext)

        var_name = str(variable.to_interface_name())
        self.init_data_refs[var_name] = variable

        return variable

    def import_from_format(self, name, semantic_type,
                           variable, view_type=None):
        imported_var = super().import_from_format(
            name, semantic_type, variable, view_type=view_type)

        interface_name = imported_var.to_interface_name()
        import_fp = variable.to_interface_name()

        lines = [
            '%s <- Artifact$import_data(' % (interface_name,),
            self.INDENT + '%r,' % (semantic_type,),
            self.INDENT + '%r,' % (import_fp,),
        ]

        if view_type is not None:
            if type(view_type) is not str:
                # Show users where these formats come from when used in the
                # Python API to make things less "magical".
                import_path = _canonical_module(view_type)
                view_type = view_type.__name__
                if import_path is not None:
                    self._update_imports(from_=import_path,
                                         import_=view_type)
                else:
                    # May be in scope already, but something is quite wrong at
                    # this point, so assume the plugin_manager is sufficiently
                    # informed.
                    view_type = repr(view_type)
            else:
                view_type = repr(view_type)

            lines.append(self.INDENT + '%s,' % (view_type,))

        lines.append(')')

        self._update_imports(from_='qiime2', import_='Artifact')
        self._add(lines)

        return imported_var

    def merge_metadata(self, name, *variables):
        variable = super().merge_metadata(name, *variables)

        first_var, remaining_vars = variables[0], variables[1:]
        first_md = first_var.to_interface_name()

        names = [str(r.to_interface_name()) for r in remaining_vars]
        remaining = ', '.join(names)
        var_name = variable.to_interface_name()

        lines = ['%r <- %r$merge(%s)' % (var_name, first_md, remaining)]

        self._add(lines)

        return variable

    def get_metadata_column(self, name, column_name, variable):
        col_variable = super().get_metadata_column(name, column_name, variable)

        to_name = col_variable.to_interface_name()
        from_name = variable.to_interface_name()

        lines = ['%s <- %s$get_column(%r)' % (to_name, from_name, column_name)]

        self._add(lines)

        return col_variable

    def view_as_metadata(self, name, from_variable):
        to_variable = super().view_as_metadata(name, from_variable)

        from_name = from_variable.to_interface_name()
        to_name = to_variable.to_interface_name()

        lines = ['%r <- %r$view(Metadata)' % (to_name, from_name)]

        self._update_imports(from_='qiime2', import_='Metadata')
        self._add(lines)

        return to_variable

    def peek(self, variable):
        var_name = variable.to_interface_name()

        lines = []
        for attr in ('uuid', 'type', 'format'):
            lines.append('print(%r$%s)' % (var_name, attr))

        self._add(lines)

        return variable

    def comment(self, text):
        lines = ['# %s' % (text,)]

        self._add(lines)

    def help(self, action):
        action_name = self._plugin_import_as_name(action)

        # TODO: this isn't pretty, but it gets the job done
        lines = ['help(%s$%s$__call__)' % (action_name, action.action_id)]

        self._add(lines)

    def action(self, action, input_opts, output_opts):
        variables = super().action(action, input_opts, output_opts)

        self._plugin_import_as_name(action)

        inputs = input_opts.map_variables(lambda v: v.to_interface_name())
        self._template_action(action, inputs, variables)

        return variables

    def get_example_data(self):
        return {r: v.execute() for r, v in self.init_data_refs.items()}

    def _plugin_import_as_name(self, action):
        action_f = action.get_action()
        full_import = action_f.get_import_path()
        base, _, _ = full_import.rsplit('.', 2)
        as_ = '%s_actions' % (action.plugin_id,)
        self._update_imports(import_='%s.actions' % (base,), as_=as_)
        return as_

    def _template_action(self, action, input_opts, variables):
        output_vars = 'action_results'

        plugin_id = action.plugin_id
        action_id = action.action_id
        lines = [
            '%s <- %s_actions$%s(' % (output_vars, plugin_id, action_id),
        ]

        for k, v in input_opts.items():
            line = self._template_input(k, v)
            lines.append(line)

        lines.append(')')

        for k, v in variables._asdict().items():
            var_name = v.to_interface_name()
            lines.append('%s <- action_results$%s' % (var_name, k))

        self._add(lines)

    def _template_input(self, input_name, value, set_var=None):
        if isinstance(value, list):
            t = self._template_collection(value)
            return self.INDENT + '%s=list(%s),' % (input_name, t)

        if isinstance(value, set):
            self._update_imports(builtins=True)
            t = self._template_collection(sorted(value, key=str))
            return self.INDENT + '%s=builtins$set(list(%s)),' % (input_name, t)

        if isinstance(value, bool):
            if value:
                t = 'TRUE'
            else:
                t = 'FALSE'

            return self.INDENT + '%s=%s,' % (input_name, t)

        if isinstance(value, int):
            return self.INDENT + '%s=%rL,' % (input_name, value)

        if value is None:
            return self.INDENT + '%s=NULL,' % (input_name,)

        return self.INDENT + '%s=%r,' % (input_name, value)

    def _template_collection(self, collection):
        template = ''
        for element in collection:
            if element is True:
                template += 'TRUE, '
            elif element is False:
                template += 'FALSE, '
            elif type(element) is int:
                template += f'{element}L, '
            elif element is None:
                template += 'NULL, '
            else:
                template += f'{repr(element)}, '

        return template.rstrip(', ')

    def _update_imports(
        self, import_=None, from_=None, as_=None, builtins=False
    ):
        if builtins:
            rendered = 'builtins <- import_builtins()'
        else:
            import_record = self.ImporterRecord(
                import_=import_, from_=from_, as_=as_)

            if as_ is not None:
                self.namespace.add(as_)
            else:
                self.namespace.add(import_)

            rendered = import_record.render()

        if rendered not in self.global_imports:
            self.local_imports.add(rendered)
            self.global_imports.add(rendered)
