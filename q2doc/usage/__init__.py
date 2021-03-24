from q2doc.usage.usage import process_usage_blocks
from q2doc.usage.directive import UsageDirective
from q2doc.usage.nodes import UsageNode, UsageExampleNode, UsageDataNode, UsageMetadataNode


def setup(app):
    app.add_directive("usage", UsageDirective)
    app.add_node(UsageNode, html=(lambda *_: None, lambda *_: None))
    app.add_node(
        UsageExampleNode, html=(lambda *_: None, UsageExampleNode.depart)
    )
    app.add_node(UsageDataNode, html=(lambda *_: None, UsageDataNode.depart))
    app.add_node(
        UsageMetadataNode, html=(lambda *_: None, UsageMetadataNode.depart)
    )
    app.add_config_value('factory', False, 'html')
    app.connect("doctree-resolved", process_usage_blocks)
