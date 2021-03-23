from q2doc.usage.usage import process_usage_blocks
from q2doc.usage.directive import (
    UsageDirective,
    UsageNode,
    UsageExampleNode,
    depart_example_node,
    UsageDataNode,
    depart_data_node,
)


def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(UsageNode, html=(lambda *_: None, lambda *_: None))
    app.add_node(UsageExampleNode, html=(lambda *_: None, depart_example_node))
    app.add_node(UsageDataNode, html=(lambda *_: None, depart_data_node))
    app.add_config_value('factory', False, 'html')
    app.connect("doctree-resolved", process_usage_blocks)
