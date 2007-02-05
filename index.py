#!/usr/bin/python

import sys

import defaults
import utils
import modules
import teams
import data
from database import *

import os

if __name__=="__main__":
    import cgi
    import cgitb; cgitb.enable()
    import l10n
    from Cheetah.Template import Template

    l10n.set_language()
    print "Content-type: text/html; charset=UTF-8\n"
    html = Template(file="templates/index.tmpl", filter=l10n.MyFilter)
    html._ = l10n.gettext
    html.rtl = (defaults.language in defaults.rtl_languages)

    print unicode(html).encode('utf-8')
    print utils.TemplateInspector(html)
