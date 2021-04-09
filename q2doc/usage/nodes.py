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
    def __init__(self, cli=None, artifact_api=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cli = cli
        self.artifact_api = artifact_api

    def prelude(self):
        prelude = '\n'.join(
            ['from qiime2 import Artifact',
             'from qiime2 import Metadata']
        )
        return f'{prelude}\n\n{self.artifact_api}'

    @staticmethod
    def depart(translator, node):
        template = jinja_env.get_template("example.html")
        rendered = template.render(node=node)
        translator.body.append(rendered)


class UsageDataNode(UsageNode):
    def __init__(self, setup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup = setup
        self.loaded = False


class FactoryNode(UsageNode):
    def __init__(
        self,
        relative_url,
        absolute_url,
        saveas,
        ref=None,
        preview=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.ref = ref
        self.relative_url = relative_url
        self.absolute_url = absolute_url
        self.saveas = saveas
        self.preview = preview

    @staticmethod
    def depart(translator, node):
        template = jinja_env.get_template('factory.html')
        rendered = template.render(node=node)
        translator.body.append(rendered)
