from q2doc.usage.usage import process_usage_blocks
from q2doc.usage.directive import UsageDirective
from q2doc.usage.nodes import (
    UsageNode,
    UsageExampleNode,
    UsageDataNode,
    UsageMetadataNode,
)


def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(UsageNode, html=(_, _))
    app.add_node(UsageExampleNode, html=(_, UsageExampleNode.depart))
    app.add_node(UsageDataNode, html=(_, UsageDataNode.depart))
    app.add_node(UsageMetadataNode, html=(_, UsageMetadataNode.depart))
    app.add_config_value('output-dir', 'results', 'html')
    app.connect("doctree-resolved", process_usage_blocks)


def _(*_):
    pass
