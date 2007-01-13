# Handle web page template and .xml localisation

from gettext import GNUTranslations, NullTranslations
import types
import Cheetah.Filters
import defaults
import accept
import os

trans = None

def get_trans():
    global trans
    if trans: return trans
    filename = 'po/%s.mo' % (defaults.language)
    try:
        fp = open(filename, 'rb')
        trans = GNUTranslations(fp=fp)
    except:
        trans = NullTranslations()
    return trans

def set_language():
    fallback = defaults.language
    linguas = open('po/LINGUAS', 'r')
    langs = ['en'] + linguas.read().split('\n')

    select = accept.language(os.getenv('HTTP_ACCEPT_LANGUAGE', fallback))
    defaults.language = select.select_from(langs)
    get_trans()

def gettext(text):
    return get_trans().ugettext(unicode(text))


def ngettext(text, plural, number):
    return get_trans().ungettext(unicode(text), unicode(plural), number)

class MyFilter(Cheetah.Filters.Filter):
    def filter(self, val, **kw):
        del kw['rawExpr']
        if type(val) in types.StringTypes:
            if kw.has_key('CAPITALIZE'):
                val = unicode(val).capitalize()
                del kw['CAPITALIZE']
            val = val.replace('%20', ' ')
            return val % kw
        else:
            return unicode(val)
