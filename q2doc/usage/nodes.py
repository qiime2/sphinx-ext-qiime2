import docutils
import jinja2

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

    @staticmethod
    def depart(translator, node):
        if not node.titles:
            return
        template = jinja_env.get_template("example.html")
        rendered = template.render(node=node)
        translator.body.append(rendered)


class UsageDataNode(UsageNode):
    def __init__(self, semantic_type, setup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semantic_type = semantic_type
        self.setup = setup

    @staticmethod
    def depart(translator, node):
        template = jinja_env.get_template("init_data.html")
        node.id = translator.document.settings.env.new_serialno('data_node')
        rendered = template.render(node=node)
        translator.body.append(rendered)


class UsageMetadataNode(UsageNode):
    def __init__(self, semantic_type, setup, preview, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semantic_type = semantic_type
        self.preview = preview
        self.setup = setup

    @staticmethod
    def depart(translator, node):
        template = jinja_env.get_template("init_metadata.html")
        node.id = translator.document.settings.env.new_serialno('data_node')
        rendered = template.render(node=node)
        translator.body.append(rendered)