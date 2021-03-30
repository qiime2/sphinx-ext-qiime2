import docutils
from sphinx.util.docutils import SphinxDirective

from q2doc.usage.nodes import UsageNode


def factory_spec(name):
    return directives.choice(name, ('data', 'metadata'))


class UsageDirective(SphinxDirective):
    has_content = True
    option_spec = {
        'factory': factory_spec,
        'name': str
    }
    # TODO Validate the spec
    #  assert v in factory.values()

    def run(self):
        code = "\n".join(self.content)
        env = self.state.document.settings.env
        if not hasattr(env, "usage_blocks"):
            env.usage_blocks = []
        factory = self.options.get('factory')
        name = self.options.get('name')
        nodes = [UsageNode(factory=factory, name=name)]
        env.usage_blocks.append(
            {"code": code,
             "nodes": nodes})
        return nodes