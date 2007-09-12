#!/usr/bin/python

import sys

import defaults
import utils
import modules
import teams
import data
from database import *

import os
from dispatcher import DamnedRequest, RequestMapper

allmodules = None

from module import ListModulesRequest, ModulePageRequest
from people import ListPeopleRequest, PersonRequest
from teams import (ListTeamsRequest, TeamRequest,
                   ListLanguagesRequest, LanguageRequest,
                   LanguageReleaseRequest)
from releases import ListReleasesRequest, ReleaseRequest

if __name__=="__main__":
    import cgi
    if defaults.DEBUG:
        import cgitb; cgitb.enable()

    mapper = RequestMapper()

    index = DamnedRequest(template="templates/index.tmpl")
    mapper.addRequest('$', index)

    list_modules = ListModulesRequest(template="templates/list-modules.tmpl")
    mapper.addRequest('modules?/?$', list_modules)

    module_page = ModulePageRequest(template="templates/module.tmpl")
    mapper.addRequest('module/(.+)$', module_page)

    list_people = ListPeopleRequest(template="templates/people.tmpl")
    mapper.addRequest('people/?$', list_people)

    show_person = PersonRequest(template="templates/person.tmpl")
    mapper.addRequest('people/(.+)$', show_person)

    list_teams = ListTeamsRequest(template="templates/list-teams.tmpl")
    mapper.addRequest('teams/?$', list_teams)

    show_team = TeamRequest(template="templates/team.tmpl")
    mapper.addRequest('teams/(.+)$', show_team)

    list_langs = ListLanguagesRequest(template="templates/list-languages.tmpl")
    mapper.addRequest('languages/?$', list_langs)

    show_language = LanguageRequest(template="templates/team.tmpl")
    mapper.addRequest('languages/([^/]+)/?$', show_language)

    show_lang_release = LanguageReleaseRequest(
        template="templates/language-release.tmpl",
        xmltemplate="templates/language-release-xml.tmpl")
    mapper.addRequest('languages/([^/]+/.+)/?$', show_lang_release)

    list_releases = ListReleasesRequest(template="templates/list-releases.tmpl")
    mapper.addRequest('releases/?$', list_releases)

    show_release = ReleaseRequest(template="templates/release.tmpl",
                                  xmltemplate="templates/release-xml.tmpl")
    mapper.addRequest('releases/(.+)/?$', show_release)

    mapper.handleAll()
