from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from q2doc.usage.nodes import UsageNode


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
        # Just add a generic placeholder node for now.
        node = UsageNode(factory=factory, name=name)
        node.docname = env.docname
        env.usage_blocks.append({"code": code, "nodes": [node]})
        return [node]
