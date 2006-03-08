#!/usr/bin/python

# real    0m1.391s
# user    0m0.927s
# sys     0m0.023s


import xml.dom.minidom
import defaults

class TranslationTeams:
    """Reads in and returns list of translation teams, or data for only a single team."""
    def __init__(self, teamsfile="translation-teams.xml", only_team=None):
        result = {}
        
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

            result[teamid] = {
                'webpage' : self.getElementText(team, 'webpage'),
                'userpage' : self.getElementText(team, 'userpage'),
                'mailing_list' : self.getMailingList(team),
                }
            result[teamid]['coordinator'] = self.getCoordinator(team)
            result[teamid]['bugzilla'] = self.getBugzillaDetails(team, teamid, firstlanguage, defaults.bugzilla)

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
            'webpage' : self.getElementText(el, 'webpage', ''),
            'cvs-account' : self.getElementText(el, 'cvs-account', ''),
            }
        coord['bugzilla-account'] = self.getElementText(el, 'cvs-account', coord['email'])
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



def TranslationLanguages(teamsfile="translation-teams.xml"):
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

        if lang.hasAttribute("hidden") and int(lang.getAttribute("hidden")):
            result[code] = ""
            pass
        else:
            result[code] = title

    return result


if __name__=="__main__":
    t = TranslationTeams()
    for teamid in t:
        import pprint
        print teamid, ":\n", pprint.pformat(t[teamid])

    #import pprint
    #pprint.pprint(TranslationLanguages())
    
