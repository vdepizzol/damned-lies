#!/usr/bin/python

import os
import utils
import defaults
import l10n

if defaults.DEBUG:
    import cgitb; cgitb.enable()

_ = l10n.gettext

from Cheetah.Template import Template

class DamnedTemplate(Template):
    def __init__(self, *args, **kw):
        content = open(kw['file'], 'r').read().decode('utf-8')
        kw['source'] = content
        if not kw.has_key('filter'):
            kw['filter'] = l10n.MyFilter
        del kw['file']
        Template.__init__(self, *args, **kw)
        self._ = l10n.gettext
        self.rtl = (defaults.language in defaults.rtl_languages)
        self.webroot = defaults.webroot

class DamnedHttpRequest:
    def __init__(self):
        l10n.set_language()
        self.request = os.getenv("PATH_INFO")[1:]
        self.content_type = 'text/html'
        if self.request.endswith('.xml'):
            self.content_type = 'application/xml'
        self.template = None

    def render(self):
        print "Content-type: %s; charset=UTF-8\n" % (self.content_type)
        print unicode(self.template).encode('utf-8')
        if self.content_type == 'text/html':
            print utils.TemplateInspector(self.template)

    def read_template(self, template):
        self.template = DamnedTemplate(file=template)
