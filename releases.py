#!/usr/bin/python

import xml.dom.minidom
import defaults
import utils
import modules
from database import *

import os

class Releases:
    """Reads in and returns list of releases, or data for only a single release."""


    def get_stats_for_module(self, module, domain, branch, language, type):
        if language:
            stats = Statistics.select(AND(Statistics.q.Module == module,
                                          Statistics.q.Domain == domain,
                                          Statistics.q.Branch == branch,
                                          Statistics.q.Language == language,
                                          Statistics.q.Type == type),
                                      orderBy="-date")
        else:
            stats = Statistics.select(AND(Statistics.q.Module == module,
                                          Statistics.q.Domain == domain,
                                          Statistics.q.Branch == branch,
                                          Statistics.q.Language == None,
                                          Statistics.q.Type == type),
                                      orderBy="-date")
            
        if stats and stats.count():
            tr = stats[0].Translated
            fz = stats[0].Fuzzy
            un = stats[0].Untranslated

            return (tr,fz,un)
        else:
            return (0,0,0)

    def list_modules(self, topnode, gather_stats = None):
        """Goes through all modules and gathers stats for language gather_stats.

        gather_stats is "None" for no regeneration and
        language code for specific language."""
        # read modules
        retmodules = {}
        pot = totaltr = totalfz = totalun = 0
        dpot = dtotaltr = dtotalfz = dtotalun = 0
        
        mods = self.getDirectSubnodes(topnode, "module")
        for mod in mods:
            modid = mod.getAttribute('id')
            branch = mod.getAttribute("branch")
            if not branch:
                branch = "HEAD"
            retmodules[modid] = {
                'id' : modid,
                'branch': branch,
                }
            
            if modid in self.myModules.keys():
                myMod = self.myModules[modid]
                retmodules[modid]['description'] = myMod['description']
                retmodules[modid]['maintainers'] = myMod['maintainers']

                if gather_stats:
                    trdomains = myMod['cvsbranches'][branch]['translation_domains']
                    documents = myMod['cvsbranches'][branch]['documents']

                    retmodules[modid]['statistics'] = { 'ui_size' : 0, 'ui_translated' : 0, 'ui_fuzzy' : 0, 'ui_untranslated' : 0,
                                                        'doc_size' : 0, 'doc_translated' : 0, 'doc_fuzzy' : 0, 'doc_untranslated' : 0 }

                    for trdomain in trdomains:
                        (tr, fz, un) = self.get_stats_for_module(modid, trdomain, branch, gather_stats, 'ui')
                        totaltr += tr; totalfz += fz; totalun += un

                        (ig1, ig2, pot_size) = self.get_stats_for_module(modid, trdomain, branch, None, 'ui')
                        pot += pot_size

                        retmodules[modid]['statistics']['ui_size'] += pot_size
                        retmodules[modid]['statistics']['ui_translated'] += tr;
                        retmodules[modid]['statistics']['ui_fuzzy'] += fz;
                        retmodules[modid]['statistics']['ui_untranslated'] += un;

                    for document in documents:
                        (tr, fz, un) = self.get_stats_for_module(modid, document, branch, gather_stats, 'doc')
                        dtotaltr += tr; dtotalfz += fz; dtotalun += un

                        (ig1, ig2, pot_size) = self.get_stats_for_module(modid, document, branch, None, 'doc')
                        dpot += pot_size

                        retmodules[modid]['statistics']['doc_size'] += pot_size
                        retmodules[modid]['statistics']['doc_translated'] += tr;
                        retmodules[modid]['statistics']['doc_fuzzy'] += fz;
                        retmodules[modid]['statistics']['doc_untranslated'] += un;

        return (pot, totaltr, totalfz, totalun, dpot, dtotaltr, dtotalfz, dtotalun, retmodules)

    def __init__(self, releasesfile="releases.xml", only_release=None, deep=1, gather_stats = None):
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
            pot = totaltr = totalfz = totalun = 0
            dpot = dtotaltr = dtotalfz = dtotalun = 0
            ui_size = doc_size = 0
            
            if deep:
                (ui_size, totaltr, totalfz, totalun, doc_size, dtotaltr, dtotalfz, dtotalun, retmodules) = self.list_modules(release, gather_stats)
                cats = self.getDirectSubnodes(release, "category")
                for cat in cats:
                    (pot, tr, fz, un, dpot, dtr, dfz, dun, catMods) = self.list_modules(cat, gather_stats)
                    ui_size += pot; totaltr += tr; totalfz += fz; totalun += un
                    doc_size += dpot; dtotaltr += dtr; dtotalfz += dfz; dtotalun += dun

                    myCat = {
                        'id' : cat.getAttribute("id"),
                        'description': self.getElementText(cat, 'description'),
                        'modules': catMods,
                        }
                    categories.append(myCat)

            if ui_size:
                totalun = ui_size - totaltr - totalfz
                ui_supp = "%.0f" % (100.0*totaltr/ui_size)
                ui_percentages = {
                    'translated': 100*totaltr/ui_size,
                    'fuzzy': 100*totalfz/ui_size,
                    'untranslated': 100*totalun/ui_size,
                    }
            else:
                ui_supp = "0"
                ui_percentages = {
                    'translated': 0,
                    'fuzzy': 0,
                    'untranslated': 0,
                    }

            if doc_size:
                dtotalun = doc_size - dtotaltr - dtotalfz
                doc_supp = "%.0f" % (100.0*dtotaltr/doc_size)
                doc_percentages = {
                    'translated': 100*dtotaltr/doc_size,
                    'fuzzy': 100*dtotalfz/doc_size,
                    'untranslated': 100*dtotalun/doc_size,
                    }
            else:
                doc_supp = "0"
                doc_percentages = {
                    'translated': 0,
                    'fuzzy': 0,
                    'untranslated': 0,
                    }

            entry = {
                'id' : releaseid,
                'description' : self.getElementText(release, 'description'),
                'modules' : retmodules,
                'categories' : categories,
                'ui_size' : ui_size,
                'ui_translated' : totaltr,
                'ui_fuzzy' : totalfz,
                'ui_untranslated' : totalun,
                'ui_supportedness' : ui_supp,
                'ui_percentages': ui_percentages,
                'doc_size' : doc_size,
                'doc_translated' : dtotaltr,
                'doc_fuzzy' : dtotalfz,
                'doc_untranslated' : dtotalun,
                'doc_supportedness' : doc_supp,
                'doc_percentages': doc_percentages,
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
            ret = node.getAttribute(attribute)
            if ret:
                return ret
            else:
                return default
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
    
