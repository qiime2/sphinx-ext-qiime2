import docutils.parsers.rst.directives


class UsageDirective(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        content = '\n'.join(self.content)
        node = docutils.nodes.literal_block(content, content)
        return [node]

def setup(app):
    app.add_directive('usage', UsageDirective)
    return {'version': '0.0.1'}
