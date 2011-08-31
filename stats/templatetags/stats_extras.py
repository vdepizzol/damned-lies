from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import get_language_bidi

from stats.models import PoFile, Statistics, FakeLangStatistics, FakeSummaryStatistics

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
def num_stats(stat, scope='full'):
    """ Produce stat numbers as in: 85% (1265/162/85) """
    if isinstance(stat, (Statistics, FakeLangStatistics, FakeSummaryStatistics)):
        stats = {
            'prc':          stat.tr_percentage(scope),
            'translated':   stat.translated(scope),
            'fuzzy':        stat.fuzzy(scope),
            'untranslated': stat.untranslated(scope),
        }
    elif isinstance(stat, PoFile):
        stats = {
            'translated':   stat.translated,
            'fuzzy':        stat.fuzzy,
            'untranslated': stat.untranslated,
        }
        if scope != 'short':
            stats['prc'] = stat.tr_percentage()
    else:
        stats = stat
    if 'translated_perc' in stats:
        stats['prc'] = stats['translated_perc']
    if 'prc' in stats:
        result = '<pre class="stats"><b>%(prc)3s%%</b> %(translated)6s %(fuzzy)5s %(untranslated)5s </pre>' % stats
        result = result.replace(" 0 ", '<span class="zero"> 0 </span>')
    else:
        result = "(%(translated)s/%(fuzzy)s/%(untranslated)s)" % stats
    return mark_safe(result)

@register.filter
def vis_stats(stat, scope='full'):
    """ Produce visual stats with green/red bar """
    if isinstance(stat, (Statistics, FakeLangStatistics, FakeSummaryStatistics)):
        trans, fuzzy, untrans = stat.tr_percentage(scope), stat.fu_percentage(scope), stat.un_percentage(scope)
    elif isinstance(stat, PoFile):
        trans, fuzzy, untrans = stat.tr_percentage(), stat.fu_percentage(), stat.un_percentage()
    else:
        trans, fuzzy, untrans = stat['translated_perc'], stat['fuzzy_perc'], stat['untranslated_perc']
    return mark_safe("""
        <div class="translated" style="width: %(trans)spx;"></div>
        <div class="fuzzy" style="%(dir)s:%(trans)spx; width:%(fuzzy)spx;"></div>
        <div class="untranslated" style="%(dir)s:%(tr_fu)spx; width: %(untrans)spx;"></div>
        """ % {
          'dir'  : get_language_bidi() and "right" or "left",
          'trans': trans,
          'fuzzy': fuzzy,
          'tr_fu': trans + fuzzy,
          'untrans': untrans,
        })

@register.filter
def is_video(fig):
    return fig['path'].endswith('.ogv')

@register.filter
def as_tr(field):
    help_html = u''
    if field.help_text:
        help_html = u'<br /><span class="helptext">%s</span>' % field.help_text
    help_link = u''
    # This is a custom attribute possibly set in forms.py
    if hasattr(field.field, 'help_link'):
        help_link = '<span class="help_link"><a href="%s"><img src="%simg/help.png" alt="help icon" width="26"></a></span>' % (
            field.field.help_link, settings.MEDIA_URL)
    errors_html = u''
    if field.errors:
        errors_html = u'<ul class="errorlist">%s</ul>' % u''.join(["<li>%s</li>" % err for err in field.errors])
    return mark_safe(u'<tr><th>%s:</th><td>%s%s%s%s</td></tr>' % (
        field.label_tag(), errors_html, field.as_widget(), help_link, help_html)
    )
