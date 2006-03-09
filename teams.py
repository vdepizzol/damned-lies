#!/usr/bin/python

import xml.dom.minidom
import defaults
import utils
import releases

import os

class TranslationTeams:
    """Reads in and returns list of translation teams, or data for only a single team."""
    def __init__(self, teamsfile=defaults.teams_xml, only_team=None, only_language=None):
        result = []
        
        dom = xml.dom.minidom.parse(teamsfile)

        teams = dom.getElementsByTagName("team")
        for team in teams:
            teamid = team.getAttribute("id")
            if only_team and teamid != only_team: continue

            # read languages
            firstlanguage = ""
            languages = {}
            langs = team.getElementsByTagName("language")
            for lang in langs:
                code = lang.getAttribute('code')
                languages[code] = {
                    'code' : code,
                    'name' : self.getElementContents(lang),
                    'hidden' : 0,
                    }
                if lang.hasAttribute('hidden'):
                    languages[code]['hidden'] = int(lang.getAttribute('hidden'))
                if not firstlanguage: firstlanguage = languages[code]['name']


            entry = {
                'id' : teamid,
                'webpage' : self.getElementText(team, 'webpage'),
                'userpage' : self.getElementText(team, 'userpage'),
                'mailing_list' : self.getMailingList(team),
                'firstlanguage' : firstlanguage,
                'languages' : languages,
                }
            entry['coordinator'] = self.getCoordinator(team)
            entry['bugzilla'] = self.getBugzillaDetails(team, teamid, firstlanguage, defaults.bugzilla)
            entry['description'] = self.getElementText(team, 'description', "%s Translation Team" % (firstlanguage))

            if only_language and only_language in languages.keys():
                self.data = [ entry ]
                return
            result.append(entry)

        if only_language:
            self.data = []
        else:
            self.data = result

    def getFirstSubnode(self, node, subnode):
        if not node.hasChildNodes():
            return None
        child = node.firstChild
        while child:
            if child.nodeType == child.ELEMENT_NODE and child.nodeName == subnode:
                return child
            child = child.nextSibling
        return None
        

    def getCoordinator(self, node):
        el = self.getFirstSubnode(node, "coordinator")
        if not el:
            return None

        coord = {
            'name' : self.getElementText(el, 'name', ''),
            'irc_nickname' : self.getElementText(el, 'irc-nickname', ''),
            'email' : self.getElementText(el, 'email', ''),
            'hackergotchi' : self.getElementText(el, 'hackergotchi', ''),
            'webpage' : self.getElementText(el, 'webpage', ''),
            'cvs_account' : self.getElementText(el, 'cvs-account', ''),
            }
        coord['bugzilla_account'] = self.getElementText(el, 'bugzilla-account', coord['email'])
        coord['im'] = []

        ims = el.getElementsByTagName("im")
        for im in ims:
            if im.hasAttribute("type"):
                coord['im'].append( (im.getAttribute("type"), self.getElementContents(im) ) )
            else:
                coord['im'].append( ("", self.getElementContents(im) ) )
        return coord
        
    def getBugzillaDetails(self, team, teamid, teamname, default = 0):
        node = self.getFirstSubnode(team, "bugzilla")
        if not node:
            return  {
                "baseurl" : default["baseurl"],
                "xmlrpc" : default["xmlrpc"],
                "product" : "l10n",
                "component" : "%s [%s]" % (teamname, teamid),
                }

        return {
           "baseurl" : self.getElementText(node, "baseurl", default["baseurl"]),
           "xmlrpc" : self.getElementText(node, "xmlrpc", default["xmlrpc"]),
           "product" : self.getElementText(node, "product", "l10n"),
           "component" : self.getElementText(node, "component", "%s [%s]" % (teamname, teamid)),
           }
            
    def getMailingList(self, team):
        node = self.getFirstSubnode(team, "mailing-list")
        if not node:
            return None

        rc = {
           "mail_to" : self.getElementText(node, "mail-to", ""),
           "subscribe" : self.getElementText(node, "subscribe", ""),
           }
        return rc
            

    def getElementContents(self, node):
        nodelist = node.childNodes
        rc = ""
        for el in nodelist:
            if el.nodeType == el.TEXT_NODE:
                rc = rc + el.data
        return rc
        
    def getElementText(self, node, element, default = 0):
        if not node.hasChildNodes():
            return default
        child = node.firstChild
        while child:
            if child.nodeType == child.ELEMENT_NODE and child.nodeName == element:
                return self.getElementContents(child)
            child = child.nextSibling
        return default
        

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

    def getElementContents(node):
        nodelist = node.childNodes
        rc = ""
        for el in nodelist:
            if el.nodeType == el.TEXT_NODE:
                rc = rc + el.data
        return rc

    result = {}

    dom = xml.dom.minidom.parse(teamsfile)

    langs = dom.getElementsByTagName("language")
    for lang in langs:
        code = lang.getAttribute("code")
        title = getElementContents(lang)

        if lang.hasAttribute("hidden") and int(lang.getAttribute("hidden")) and not show_hidden:
            #result[code] = ""
            pass
        else:
            result[code] = title

    return result


def compare_teams(a, b):
    res = cmp(a['firstlanguage'], b['firstlanguage'])
    if not res:
        return cmp(a['code'], b['code'])
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
            if len(myteam) and myteam[0]['id'] == teamid:
                html = Template(file="templates/team.tmpl")
                team = myteam[0]

                for lang, ldata in team['languages'].items():
                    team['languages'][lang]['releases'] = releases.Releases(deep=1, gather_stats = lang).data

                html.webroot = defaults.webroot
                html.team = team

                print html
                print utils.TemplateInspector(html)
        else:
            t = TranslationTeams()
            teams = t.data
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
            if len(myteam) and myteam[0]['id']:
                team = myteam[0]
                teamid = team['id']

                for lang, ldata in team['languages'].items():
                    if lang != langid:
                        del team['languages'][lang]

                if release:
                    html = Template(file="templates/language-release.tmpl")
                    html.language = langid
                    html.language_name = team['languages'][langid]['name']
                    html.release = releases.Releases(deep=1, only_release = release, gather_stats = langid).data[0]
                    
                else:
                    html = Template(file="templates/team.tmpl")
                    team['languages'][langid]['releases'] = releases.Releases(deep=1, gather_stats = langid).data
                    

                html.webroot = defaults.webroot
                html.team = team

                print html
                print utils.TemplateInspector(html)
            else:
                print "Error: Can't find translation team for '%s'." % langid

    #import pprint
    #pprint.pprint(TranslationLanguages())
    
