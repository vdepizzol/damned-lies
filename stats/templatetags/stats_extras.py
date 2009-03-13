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
