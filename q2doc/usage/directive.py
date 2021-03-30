import docutils
from sphinx.util.docutils import SphinxDirective

from q2doc.usage.nodes import UsageNode


class UsageDirective(SphinxDirective):
    has_content = True
    option_spec = {'factory': docutils.parsers.rst.directives.flag}
        'name': str

    def run(self):
        code = "\n".join(self.content)
        env = self.state.document.settings.env
        if not hasattr(env, "usage_blocks"):
            env.usage_blocks = []
        env.usage_blocks.append({"code": code})
        factory = "factory" in self.options
        return [UsageNode(factory=factory)]
        name = self.options.get('name')
        nodes = [UsageNode(factory=factory, name=name)]
        env.usage_blocks.append(
            {"code": code,
             "nodes": nodes})
        return nodes