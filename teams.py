#!/usr/bin/python

import xml.dom.minidom
import defaults
import utils
import releases

import data

import os

class TranslationTeams:
    """Reads in and returns list of translation teams, or data for only a single team."""
    def __init__(self, teamsfile=defaults.teams_xml, only_team=None, only_language=None):

        teams =  data.getTeams(only_team)
        people =  data.getPeople()

        for teamid in teams.keys():
            firstlanguage = ""

            for lang in teams[teamid]['language'].keys():
                if not firstlanguage:
                    firstlanguage = teams[teamid]['language'][lang]['content']

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


        self.data = teams
        

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


if __name__=="__main__":
    import cgi, re
    import cgitb; cgitb.enable()
    from Cheetah.Template import Template

    print "Content-type: text/html; charset=UTF-8"

    request = os.getenv("PATH_INFO")[1:]
    test = re.match("([^/]+)(/(.+)/?)?", request)
    if not test:
        utils.not_found_404()
    
    page = test.groups()[0]
    subrequest = test.groups()[2]

    teamid = langid = release = None

    if page == "teams":
        teamid = subrequest
        print ""

        if teamid:
            myteam = TranslationTeams(only_team=teamid)
            if len(myteam) and myteam.data.has_key(teamid):
                html = Template(file="templates/team.tmpl")
                team = myteam.data[teamid]

                for lang, ldata in team['language'].items():
                    team['language'][lang]['releases'] = releases.Releases(deep=1, gather_stats = lang).data

                html.webroot = defaults.webroot
                html.team = team

                print html
                print utils.TemplateInspector(html)
        else:
            t = TranslationTeams()
            teams = []
            for tid, team in t.data.items():
                teams.append(team)
            teams.sort(compare_teams)

            html = Template(file="templates/list-teams.tmpl")
            html.webroot = defaults.webroot
            html.teams = teams
            print html
            print utils.TemplateInspector(html)

    elif page == "languages":
        print ""

        if subrequest:
            test = re.match("([^/]+)(/(.+)/?)?", subrequest)
        else: test = None
        if not test:
            # List all languages (FIXME)

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

            html = Template(file="templates/list-languages.tmpl")
            html.webroot = defaults.webroot
            html.languages = langs
            print html
            print utils.TemplateInspector(html)

        else:
            langid = test.groups()[0]
            release = test.groups()[2]

            #print "page: %s<br/>langid: %s<br/>release: %s<br/>" % (page, langid, release)
            myteam = TranslationTeams(only_language=langid)
            # FIXME: get language instead of team

            if len(myteam):
                teamid = myteam.data.keys()[0]
                team = myteam.data[teamid]
                #teamid = team['id']

                for lang, ldata in team['language'].items():
                    if lang != langid:
                        del team['language'][lang]

                if release:
                    html = Template(file="templates/language-release.tmpl")
                    html.language = langid
                    html.language_name = team['language'][langid]['content']
                    html.release = releases.Releases(deep=1, only_release = release, gather_stats = langid).data[0]
                    
                else:
                    html = Template(file="templates/team.tmpl")
                    team['language'][langid]['releases'] = releases.Releases(deep=1, gather_stats = langid).data
                    

                html.webroot = defaults.webroot
                html.team = team
                if not html.team.has_key('description') and html.language_name:
                    html.team['description'] = html.language_name + " Translation Team"
                if not html.team.has_key('bugzilla-component') and html.language_name:
                    html.team['bugzilla-component'] = html.language_name + " [%s]" % (langid)

                print html
                print utils.TemplateInspector(html)
            else:
                print myteam.data
                print "Error: Can't find translation team for '%s'." % langid

    #import pprint
    #pprint.pprint(TranslationLanguages())
    
