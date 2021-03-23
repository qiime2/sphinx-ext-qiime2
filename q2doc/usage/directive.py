import jinja2
import docutils
from sphinx.util.docutils import SphinxDirective


loader = jinja2.PackageLoader("q2doc.usage", "templates")
jinja_env = jinja2.Environment(loader=loader)


class UsageNode(docutils.nodes.General, docutils.nodes.Element):
    def __init__(self, factory=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.factory = factory


class UsageExampleNode(UsageNode):
    def __init__(self, titles=[], examples=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.titles = titles
        self.examples = examples


class UsageDataNode(UsageNode):
    def __init__(self, semantic_type, preview, setup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semantic_type = semantic_type
        self.preview = preview
        self.setup = setup


class UsageDirective(SphinxDirective):
    has_content = True
    option_spec = {'factory': docutils.parsers.rst.directives.flag}

    def run(self):
        code = "\n".join(self.content)
        env = self.state.document.settings.env
        if not hasattr(env, "usage_blocks"):
            env.usage_blocks = []
        env.usage_blocks.append({"code": code})
        factory = "factory" in self.options
        return [UsageNode(factory=factory)]


def depart_example_node(self, node):
    if not node.titles:
        return
    template = jinja_env.get_template("example.html")
    rendered = template.render(node=node)
    self.body.append(rendered)


def depart_data_node(self, node):
    template = jinja_env.get_template("data.html")
    node.id = self.document.settings.env.new_serialno('data_node')
    rendered = template.render(node=node)
    self.body.append(rendered)
