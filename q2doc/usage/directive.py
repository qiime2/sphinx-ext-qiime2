from docutils.parsers.rst import directives
from sphinx.domains import Domain
from sphinx.util.docutils import SphinxDirective

from q2doc.usage.nodes import UsageNode, UsageDataNode, UsageExampleNode, FactoryNode
from q2cli.core.usage import CLIUsage
from qiime2.plugins import ArtifactAPIUsage
from qiime2.sdk import usage as usage


def factory_spec(name):
    return directives.choice(name, ('data', 'metadata'))


class UsageDirective(SphinxDirective):
    has_content = True
    option_spec = {'factory': factory_spec, 'name': str}
    name = 'q2:usage'

    def run(self):
        code = "\n".join(self.content)
        env = self.state.document.settings.env
        if not hasattr(env, "usage_blocks"):
            env.usage_blocks = []
        if not hasattr(env, "rendered"):
            env.rendered = {'cli': '', 'art_api': ''}
        factory = self.options.get('factory')
        name = self.options.get('name')
        node = UsageNode(factory=factory, name=name)
        node.docname = env.docname
        env.usage_blocks.append({"code": code, "nodes": [node]})
        return [node]


class QIIME2Domain(Domain):
    name = 'q2'
    label = 'QIIME 2 Domain'

    directives = {
        'usage': UsageDirective
    }

    initial_data = {
        'drivers': {
        'dia_use': usage.DiagnosticUsage,
        'exc_use': usage.ExecutionUsage,
        'cli_use': CLIUsage,
        'art_use': ArtifactAPIUsage,
        },
    }