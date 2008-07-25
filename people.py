#!/usr/bin/env python

import sys

import defaults
import modules
import teams
import data

from dispatcher import DamnedRequest

class ListPeopleRequest(DamnedRequest):
    def __init__(self, template=None, xmltemplate=None):
        DamnedRequest.__init__(self, template, xmltemplate)
        self.people = data.getPeople()

class PersonRequest(DamnedRequest):
    def render(self, type='html'):
        personid = self.request
        people = data.getPeople()
        person = people[personid]
        self.roles = self.get_roles_for(person)
        self.person = person
        DamnedRequest.render(self, type)

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

        return { 'maintains' : maintains,
                 'translates' : translates,
                 'special' : special }

if __name__=="__main__":
    import cgi
    DamnedPeople().render()
