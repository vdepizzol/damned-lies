#!/usr/bin/python

import sys

import defaults
import modules
import teams
import data

from dispatcher import DamnedHttpRequest

class DamnedPeople(DamnedHttpRequest):
    def __init__(self):
        DamnedHttpRequest.__init__(self)
        personid = self.request or None
        persons = data.getPeople()

        if personid and len(persons) and persons.has_key(personid):
            self.read_template("templates/person.tmpl")
            self.template.person = persons[personid]
            self.template.roles = self.get_roles_for(self.template.person)
        else:
            self.read_template("templates/people.tmpl")
            self.template.people = persons

    def get_roles_for(self, person):

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
    DamnedPeople().render()
