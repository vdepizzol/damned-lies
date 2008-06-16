#!/usr/bin/python

import xml.dom.minidom
import defaults
import utils
import releases
import l10n

from dispatcher import DamnedTemplate
_ = l10n.gettext

import data

import os, re

class TranslationTeams:
    """Reads in and returns list of translation teams, or data for only a single team."""
    def __init__(self, teamsfile=defaults.teams_xml, only_team=None, only_language=None):

        teams =  data.getTeams(only_team)
        # Need to read original English file to be able to compute Bugzilla component name
        teams_en = data.getTeams(only_team,en=True)
        people =  data.getPeople()

        for teamid in teams.keys():
            firstlanguage = firstlanguage_en = ""

            for lang in teams[teamid]['language'].keys():
                if not firstlanguage:
                    firstlanguage = teams[teamid]['language'][lang]['content']
                    firstlanguage_en = teams_en[teamid]['language'][lang]['content']

            if not teams[teamid].has_key('description'):
                teams[teamid]['description'] = firstlanguage
            
            if not teams[teamid].has_key('bugzilla-component'):
                teams[teamid]['bugzilla-component'] = (firstlanguage_en
                                                  + " [%s]" % (teamid))

            coordinator = None
            coordid = teams[teamid]['coordinator'].keys()[0]
            coordinator = people[coordid]

            teams[teamid]['firstlanguage'] = firstlanguage
            teams[teamid]['coordinator'] = coordinator


            if only_language and only_language in teams[teamid]['language'].keys():
                for lang in teams[teamid]['language'].keys():
                    if lang != only_language:
                        del teams[teamid]['language'][lang]
                self.data = { teamid : teams[teamid] }
                return

        if only_language:
            self.data = {} # No team found
        else:
            self.data = teams # All teams


    # Implement dictionary methods
    def __getitem__(self, key): return self.data[key]

    def __setitem__(self, key, value): self.data[key] = value

    def __len__(self): return len(self.data)

    def keys(self): return self.data.keys()

    def has_key(self, key): return self.data.has_key(key)

    def items(self): return self.data.items()

    def values(self): return self.data.values()

    def __iter__(self): return self.data.__iter__()


def TranslationLanguages(teamsfile=defaults.teams_xml, show_hidden=0):
    """Reads in and returns a list of all languages any team is translating to."""

    teams =  data.getTeams()
    people =  data.getPeople()

    languages = {}
    
    for teamid in teams.keys():
        firstlanguage = ""

        for lang in teams[teamid]['language'].keys():
            hidden = 0
            if teams[teamid]['language'][lang].has_key('hidden'):
                hidden = teams[teamid]['language'][lang]['hidden']
            if not hidden or show_hidden:
                languages[lang] = teams[teamid]['language'][lang]['content']

    return languages

def compare_teams(a, b):
    res = cmp(a['firstlanguage'], b['firstlanguage'])
    if not res:
        return cmp(a['id'], b['id'])
    else:
        return res

def compare_releases(a, b):
    release_order = {
        "official": 1,
        "unofficial": 2,
        "external":3
    }
    a_stat = release_order.get(a['status'])
    b_stat = release_order.get(b['status'])
    res = cmp(a_stat, b_stat)
    if not res:
        if a_stat==1:
            return cmp(b['id'], a['id'])
        else:
            return cmp(a['id'], b['id'])
    else:
        return res


from dispatcher import DamnedRequest
class ListTeamsRequest(DamnedRequest):
    def render(self, type='html'):
        t = TranslationTeams()
        teams = []
        for tid, team in t.data.items():
            teams.append(team)
        teams.sort(compare_teams)
        self.teams = teams

        DamnedRequest.render(self, type)

class TeamRequest(DamnedRequest):
    def render(self, type='html'):
        teamid = self.request
        langid = None
        if teamid:
            teams = TranslationTeams(only_team=teamid)
            if len(teams) and teams.data.has_key(teamid):
                team = teams.data[teamid]

                for lang, ldata in team['language'].items():
                    releaselist = releases.Releases(deep=1, gather_stats = lang).data
                    releaselist.sort(compare_releases)
                    team['language'][lang]['releases'] = releaselist
                    if not langid: langid = lang

                language_name = team['language'][lang]['content']
                self.team = team
                self.language = lang
                self.language_name = language_name

        DamnedRequest.render(self, type)

class ListLanguagesRequest(DamnedRequest):
    def render(self, type='html'):
        t = TranslationLanguages()
        langs = []
        for lang, lname in t.items():
            langs.append( {'code' : lang, 'name' : lname } )

        def compare_langs(a, b):
            res = cmp(a['name'], b['name'])
            if not res:
                return cmp(a['code'], b['code'])
            else:
                return res

        langs.sort(compare_langs)

        self.languages = langs

        DamnedRequest.render(self, type)

class LanguageReleaseRequest(DamnedRequest):
    def render(self, type='html'):
        if self.request:
            test = re.match("([^/]+)(/(.+)/?)?", self.request)
        else: test = None

        langid = test.groups()[0]
        release = test.groups()[2]
        if release:
            (t_rel, t_ext) = os.path.splitext(release)
            if t_ext == '.xml':
                release = t_rel
        else:
            (t_rel, t_ext) = (None, None)
            print "Release not found!"
            return
        
        myteam = TranslationTeams(only_language=langid)
        if len(myteam):
            teamid = myteam.data.keys()[0]
            team = myteam.data[teamid]

            if not langid:
                for lang, ldata in team['language'].items():
                    if lang != langid:
                        del team['language'][lang]

            language_name = team['language'][langid]['content']

            if not team.has_key('description') and language_name:
                team['description'] = ( _("%(lang)s Translation Team")
                                        % { 'lang' : language_name } )
            if not team.has_key('bugzilla-component') and language_name:
                team['bugzilla-component'] = "%s [%s]" % (language_name,
                                                          langid)

            self.language_name = language_name
            self.team = team
        else:
            self.team = None
        
        myreleases = releases.Releases(deep=1, only_release=release,
                                       gather_stats=langid).data
        if myreleases:
            self.release = myreleases[0]
        else:
            print "Release not found!!"
        self.language = langid

        DamnedRequest.render(self, type)

class LanguageRequest(DamnedRequest):
    def render(self, type='html'):
        langid = self.request
        myteam = TranslationTeams(only_language=langid)
        if len(myteam):
            teamid = myteam.data.keys()[0]
            team = myteam.data[teamid]

            if not langid:
                for lang, ldata in team['language'].items():
                    if lang != langid:
                        del team['language'][lang]

            self.language = langid
            self.language_name = team['language'][langid]['content']
            releaselist = releases.Releases(deep=1, gather_stats = langid).data
            releaselist.sort(compare_releases)
            team['language'][langid]['releases'] = releaselist
            self.team = team

            DamnedRequest.render(self, type)

