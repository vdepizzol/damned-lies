from django import template

register = template.Library()

def linked_with(value, arg):
    """ This filter returns an object (passed in value) enclosed with his absolute url 
        arg is the linked text """
    return "<a href='%s'>%s</a>" % (value.get_absolute_url(), arg)

register.filter(linked_with)
