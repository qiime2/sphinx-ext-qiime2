from sphinx.domains import Domain

from q2cli.core.usage import CLIUsage
from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import usage as usage

from .directive import UsageDirective


class QIIME2Domain(Domain):
    name = 'q2'
    label = 'QIIME 2 Domain'

    directives = {'usage': UsageDirective}

    initial_data = {
        'drivers': {
            'dia_use': usage.DiagnosticUsage,
            'exc_use': usage.ExecutionUsage,
            'cli_use': CLIUsage,
            'art_use': ArtifactAPIUsage,
        },
    }
