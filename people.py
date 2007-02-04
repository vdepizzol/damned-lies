#!/usr/bin/python

import sys

import defaults
import utils
import modules
import teams
import data
from database import *

import os

def get_roles_for(person):

    translates = []
    maintains = []
    special = []

    t = teams.TranslationTeams()
    for team in t:
        myteam = t[team]
        if myteam.has_key('coordinator') and myteam['coordinator']['id'] == person['id']:
            translates.append(myteam)

    m = modules.XmlModules()
    for module in m:
        mymod = m[module]
        if mymod.has_key('maintainer') and person['id'] in mymod['maintainer'].keys():
            maintains.append(mymod)

        for obfuscate in ['email', 'bugzilla-account']:
            if person.has_key(obfuscate):
                person['nospam' + obfuscate] = person[obfuscate].replace(
                    '@', ' at ').replace('.', ' dot ')

    return { 'maintains' : maintains,
             'translates' : translates,
             'special' : special }


if __name__=="__main__":
    import cgi
    import cgitb; cgitb.enable()
    import l10n
    from Cheetah.Template import Template

    l10n.set_language()
    print "Content-type: text/html; charset=UTF-8\n"

    if os.getenv("PATH_INFO"):
        personid = os.getenv("PATH_INFO")[1:]
    else:
        personid = None

    persons = data.getPeople()
    if personid and len(persons) and persons.has_key(personid):
        import l10n
        html = Template(file="templates/person.tmpl", filter=l10n.MyFilter)
        html._ = l10n.gettext
        html.webroot = defaults.webroot
        html.person = persons[personid]
        html.roles = get_roles_for(html.person)

        print unicode(html).encode('utf-8')
        print utils.TemplateInspector(html)
    else:
        import l10n
        html = Template(file="templates/people.tmpl", filter=l10n.MyFilter)
        html._ = l10n.gettext
        html.webroot = defaults.webroot
        html.people = persons
        #html.roles = get_roles_for(html.person)

        print unicode(html).encode('utf-8')
        print utils.TemplateInspector(html)

