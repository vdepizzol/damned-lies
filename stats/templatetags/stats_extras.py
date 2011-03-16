from django import template
from django.utils.safestring import mark_safe

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

@register.filter
def browse_bugs(module, content):
    return module.get_bugs_i18n_url(content)

@register.filter
def num_stats(stat, scope):
    """ Produce stat numbers as in: 85% (1265/162/85) """
    return mark_safe("%s%%&nbsp;(%s/%s/%s)" % (
        stat.tr_percentage(scope), stat.translated(scope),
        stat.fuzzy(scope), stat.untranslated(scope))
    )
