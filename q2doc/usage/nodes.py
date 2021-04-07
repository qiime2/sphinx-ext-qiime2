import docutils
import jinja2

loader = jinja2.PackageLoader("q2doc.usage", "templates")
jinja_env = jinja2.Environment(loader=loader)


class UsageNode(docutils.nodes.General, docutils.nodes.Element):
    def __init__(self, factory=False, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.factory = factory
        self.name = name


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
    def __init__(self, setup, preview, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.preview = preview
        self.setup = setup

    @staticmethod
    def depart(translator, node):
        template = jinja_env.get_template("init_metadata.html")
        node.id = translator.document.settings.env.new_serialno('data_node')
        rendered = template.render(node=node)
        translator.body.append(rendered)


class FactoryNode(docutils.nodes.Element):
    def __init__(self, id_, relative_url, absolute_url, saveas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id_
        self.relative_url = relative_url
        self.absolute_url = absolute_url
        self.saveas = saveas

    @staticmethod
    def depart(translator, node):
        template = jinja_env.get_template('factory.html')
        rendered = template.render(node=node)
        translator.body.append(rendered)
