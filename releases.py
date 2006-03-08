#!/usr/bin/python

import xml.dom.minidom
import defaults
import utils
import modules

import os

class Releases:
    """Reads in and returns list of releases, or data for only a single release."""

    def list_modules(self, topnode):
        # read modules
        retmodules = {}
        mods = self.getDirectSubnodes(topnode, "module")
        for mod in mods:
            modid = mod.getAttribute('id')
            retmodules[modid] = {
                'id' : modid,
                'branch': self.getElementAttribute(mod, "branch", "HEAD"),
                }
            if modid in self.myModules.keys():
                myMod = self.myModules[modid]
                retmodules[modid]['description'] = myMod['description']
                retmodules[modid]['maintainers'] = myMod['maintainers']
                #retmodules[modid]['pot_messages'] = myMod['pot_messages']
        return retmodules

    def __init__(self, releasesfile="releases.xml", only_release=None, deep=1):
        result = []
        
        dom = xml.dom.minidom.parse(releasesfile)

        myModules = modules.XmlModules("gnome-modules.xml")
        self.myModules = myModules
        
        releases = dom.getElementsByTagName("release")
        for release in releases:
            releaseid = release.getAttribute("id")
            if only_release and releaseid != only_release: continue

            # read modules
            categories = []
            retmodules = []
            if deep:
                retmodules = self.list_modules(release)

                cats = self.getDirectSubnodes(release, "category")
                for cat in cats:
                    myCat = {
                        'id' : cat.getAttribute("id"),
                        'description': self.getElementText(cat, 'description'),
                        'modules': self.list_modules(cat)
                        }
                    categories.append(myCat)


            entry = {
                'id' : releaseid,
                'description' : self.getElementText(release, 'description'),
                'modules' : retmodules,
                'categories' : categories,
                }
            result.append(entry)

        self.data = result
        
    def getDirectSubnodes(self, node, subnode):
        if not node.hasChildNodes():
            return None
        results = []
        child = node.firstChild
        while child:
            if child.nodeType == child.ELEMENT_NODE and child.nodeName == subnode:
                results.append(child)
            child = child.nextSibling
        return results
        

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
        
        
    def getElementAttribute(self, node, attribute, default = 0):
        if not node.hasAttribute(attribute):
            return node.getAttribute(attribute)
        else:
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


def compare_releases(a, b):
    res = cmp(a['firstlanguage'], b['firstlanguage'])
    if not res:
        return cmp(a['code'], b['code'])
    else:
        return res

if __name__=="__main__":
    import cgi
    import cgitb; cgitb.enable()
    from Cheetah.Template import Template

    print "Content-type: text/html; charset=UTF-8\n"

    releaseid = os.getenv("PATH_INFO")[1:]
    if releaseid:
        myrelease = TranslationReleases(only_release=releaseid)
        if len(myrelease) and myrelease[0]['id'] == releaseid:
            html = Template(file="templates/release.tmpl")
            html.webroot = defaults.webroot
            html.release = myrelease[0]
            print html
            print utils.TemplateInspector(html)
    else:
        t = TranslationReleases()
        releases = t.data
        releases.sort(compare_releases)

        html = Template(file="templates/list-releases.tmpl")
        html.webroot = defaults.webroot
        html.releases = releases
        print html
        print utils.TemplateInspector(html)

    #import pprint
    #pprint.pprint(TranslationLanguages())
    
