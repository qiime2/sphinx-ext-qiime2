from q2doc.usage.usage import process_usage_blocks
from q2doc.usage.directive import UsageDirective
from q2doc.usage.nodes import (
    UsageNode,
    UsageExampleNode,
    UsageDataNode,
    FactoryNode,
)


def setup(app):
    app.add_config_value('base_url', 'http://localhost:8000/', 'html')
    app.add_directive("usage", UsageDirective)
    app.add_node(UsageNode, html=(_, _))
    app.add_node(UsageDataNode, html=(_, _))
    app.add_node(FactoryNode, html=(_, FactoryNode.depart))
    app.add_node(UsageExampleNode, html=(_, UsageExampleNode.depart))
    app.connect("doctree-resolved", process_usage_blocks)


def _(*_):
    pass
