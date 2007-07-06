# Handle web page template and .xml localisation

from gettext import GNUTranslations, NullTranslations
import types
import Cheetah.Filters
import defaults
import accept
import os
import re

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

    # in browsers, country code is separated from language with an hyphen
    langs=[lang.replace('_','-') for lang in langs]
    select = accept.language(os.getenv('HTTP_ACCEPT_LANGUAGE', fallback))
    defaults.language = select.select_from(langs).replace('-','_')
    get_trans()

def gettext(text):
    if type(text) != type(u""):
        text = unicode(text,'utf-8')
    matches = re.findall('###([^#]*)###',text) 
    if matches:
        text = re.sub('###([^#]*)###', '%s', text)

    text = get_trans().ugettext(text)
    
    #FIXME: if multiple substitutions, works only if order of %s is unchanged in translated string
    for match in matches:
    	  text = text.replace('%s',match,1)
    return text

def ngettext(text, plural, number):
    if type(text) != type(u""):
        text = unicode(text,'utf-8')
    if type(plural) != type(u""):
        plural = unicode(plural,'utf-8')

    return get_trans().ungettext(text, plural, number)

class MyFilter(Cheetah.Filters.Filter):
    def filter(self, val, **kw):
        del kw['rawExpr']
        if type(val) in types.StringTypes:
            if kw.has_key('CAPITALIZE'):
                val = unicode(val).capitalize()
                del kw['CAPITALIZE']
            val = val.replace(u'%20', ' ')
            return val % kw
        else:
            return unicode(val)
