from django import template

register = template.Library()

@register.filter
def linked_with(value, arg):
    """ This filter returns an object (passed in value) enclosed with his absolute url
        arg is the linked text """
    return "<a href='%s'>%s</a>" % (value.get_absolute_url(), arg)

@register.filter
def support_class(value):
    """ Returns a class depending on the coverage of the translation stats.
        Value is a translation percentage """
    if value >= 80:
        return "supported"
    elif value >= 50:
        return "partially"
    return "not_supported"

@register.filter
def escapeat(value):
    """Replace '@' with '__', accepted sequence in JS ids."""
    return value.replace('@', '__')

@register.filter
def domain_type(stat):
    return stat.domain.get_type(stat.branch)

class IfLessNode(template.Node):
    def __init__(self, val1, val2, nodelist_true, nodelist_false):
        self.val1 = val1
        self.val2 = val2
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        if self.val1.resolve(context) < self.val2.resolve(context):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

@register.tag
def ifless(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes two arguments" % bits[0]
    nodelist_true = parser.parse(('else', 'endifless'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifless',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfLessNode(parser.compile_filter(bits[1]), parser.compile_filter(bits[2]), nodelist_true, nodelist_false)
