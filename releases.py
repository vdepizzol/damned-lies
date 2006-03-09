#!/usr/bin/python

import xml.dom.minidom

import defaults
import utils
import modules
import teams
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
                                          Statistics.q.Type == type))
        else:
            stats = Statistics.select(AND(Statistics.q.Module == module,
                                          Statistics.q.Domain == domain,
                                          Statistics.q.Branch == branch,
                                          Statistics.q.Language == None,
                                          Statistics.q.Type == type))
            
        if stats and stats.count():
            tr = stats[0].Translated
            fz = stats[0].Fuzzy
            un = stats[0].Untranslated

            msgs = []
            for msg in stats[0].Messages:
                msgs.append( (msg.Type, msg.Description) )

            return (tr,fz,un, msgs)
        else:
            return (0,0,0,[])

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
                retmodules[modid]['cvsmodule'] = myMod['cvsmodule']

                if gather_stats and myMod['cvsbranches'].has_key(branch):
                    trdomains = myMod['cvsbranches'][branch]['translation_domains']
                    documents = myMod['cvsbranches'][branch]['documents']

                    retmodules[modid]['statistics'] = { 'ui_size' : 0, 'ui_translated' : 0, 'ui_fuzzy' : 0, 'ui_untranslated' : 0,
                                                        'doc_size' : 0, 'doc_translated' : 0, 'doc_fuzzy' : 0, 'doc_untranslated' : 0 }
                    
                    retmodules[modid]['translation_domains'] = {}
                    retmodules[modid]['documents'] = {}

                    mytr = myfz = myun = mypot = 0
                    for trdomain in trdomains:
                        (tr, fz, un, msgs) = self.get_stats_for_module(modid, trdomain, branch, gather_stats, 'ui')
                        totaltr += tr; totalfz += fz; totalun += un
                        mytr += tr; myfz += fz; myun += un

                        (ig1, ig2, pot_size, potmsgs) = self.get_stats_for_module(modid, trdomain, branch, None, 'ui')
                        pot += pot_size
                        mypot += pot_size

                        un = pot_size - tr - fz
                        if pot_size:
                            perc = { 'translated' : 100*tr/pot_size, 'fuzzy' : 100*fz/pot_size, 'untranslated' : 100*un/pot_size }
                        else:
                            perc = { 'translated' : 0, 'fuzzy' : 0, 'untranslated' : 0 }
                            
                        retmodules[modid]['translation_domains'][trdomain] = { 'translated' : tr,
                                                                               'fuzzy' : fz,
                                                                               'untranslated' : pot_size-tr-fz,
                                                                               'percentages' : perc,
                                                                               'supportedness' : perc['translated'],
                                                                               'pot_size' : pot_size,
                                                                               'pot_messages' : potmsgs,
                                                                               'po_messages' : msgs,
                                                                               'potbase' : trdomains[trdomain]['potbase'],
                                                                               'description' : trdomains[trdomain]['description'],
                                                                               }
                    if mypot:
                        myun = mypot - mytr - myfz; ui_supp = "%.0f" % (100.0*mytr/mypot)
                        ui_percentages = { 'translated': 100*mytr/mypot, 'fuzzy': 100*myfz/mypot, 'untranslated': 100*myun/mypot }
                    else:
                        myun = mypot; ui_supp = "0"
                        ui_percentages = { 'translated': 0, 'fuzzy': 0, 'untranslated': 0 }

                    retmodules[modid]['statistics']['ui_size'] = mypot
                    retmodules[modid]['statistics']['ui_translated'] = mytr
                    retmodules[modid]['statistics']['ui_fuzzy'] = myfz
                    retmodules[modid]['statistics']['ui_untranslated'] = myun
                    retmodules[modid]['statistics']['ui_percentages'] = ui_percentages
                    retmodules[modid]['statistics']['ui_supportedness'] = ui_supp

                    mytr = myfz = myun = mypot = 0
                    for document in documents:
                        (tr, fz, un, msgs) = self.get_stats_for_module(modid, document, branch, gather_stats, 'doc')
                        dtotaltr += tr; dtotalfz += fz; dtotalun += un
                        mytr += tr; myfz += fz; myun += un

                        (ig1, ig2, pot_size, potmsgs) = self.get_stats_for_module(modid, document, branch, None, 'doc')
                        dpot += pot_size
                        mypot += pot_size

                        un = pot_size - tr - fz
                        if pot_size:
                            perc = { 'translated' : 100*tr/pot_size, 'fuzzy' : 100*fz/pot_size, 'untranslated' : 100*un/pot_size }
                        else:
                            perc = { 'translated' : 0, 'fuzzy' : 0, 'untranslated' : 0 }

                        retmodules[modid]['documents'][document] = { 'translated' : tr,
                                                                     'fuzzy' : fz,
                                                                     'untranslated' : pot_size-tr-fz,
                                                                     'percentages' : perc,
                                                                     'supportedness' : perc['translated'],
                                                                     'pot_size' : pot_size,
                                                                     'pot_messages' : potmsgs,
                                                                     'po_messages' : msgs,
                                                                     'potbase' : documents[document]['potbase'],
                                                                     'description' : documents[document]['description'],
                                                                     }
                    if mypot:
                        myun = mypot - mytr - myfz; doc_supp = "%.0f" % (100.0*mytr/mypot)
                        doc_percentages = { 'translated': 100*mytr/mypot, 'fuzzy': 100*myfz/mypot, 'untranslated': 100*myun/mypot }
                    else:
                        myun = mypot; doc_supp = "0"
                        doc_percentages = { 'translated': 0, 'fuzzy': 0, 'untranslated': 0 }

                    retmodules[modid]['statistics']['doc_size'] = mypot
                    retmodules[modid]['statistics']['doc_translated'] = mytr
                    retmodules[modid]['statistics']['doc_fuzzy'] = myfz
                    retmodules[modid]['statistics']['doc_untranslated'] = myun
                    retmodules[modid]['statistics']['doc_percentages'] = doc_percentages
                    retmodules[modid]['statistics']['doc_supportedness'] = doc_supp


        return (pot, totaltr, totalfz, totalun, dpot, dtotaltr, dtotalfz, dtotalun, retmodules)

    def __init__(self, releasesfile=defaults.releases_xml, only_release=None, deep=1, gather_stats = None):
        result = []
        
        dom = xml.dom.minidom.parse(releasesfile)

        myModules = modules.XmlModules(defaults.modules_xml)
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

                    if pot:
                        un = pot - tr - fz; ui_supp = "%.0f" % (100.0*tr/pot)
                        ui_percentages = { 'translated': 100*tr/pot, 'fuzzy': 100*fz/pot, 'untranslated': 100*un/pot }
                    else:
                        un = pot; ui_supp = "0"
                        ui_percentages = { 'translated': 0, 'fuzzy': 0, 'untranslated': 0 }

                    if dpot:
                        dun = dpot - dtr - dfz; doc_supp = "%.0f" % (100.0*dtr/dpot)
                        doc_percentages = { 'translated': 100*dtr/dpot, 'fuzzy': 100*dfz/dpot, 'untranslated': 100*dun/dpot }
                    else:
                        dun = pot; doc_supp = "0"
                        doc_percentages = { 'translated': 0, 'fuzzy': 0, 'untranslated': 0 }
                    myCat['statistics'] = {
                        'ui_size' : pot,
                        'ui_translated' : tr,
                        'ui_fuzzy' : fz,
                        'ui_untranslated' : un,
                        'ui_supportedness' : ui_supp,
                        'ui_percentages': ui_percentages,
                        'doc_size' : dpot,
                        'doc_translated' : dtr,
                        'doc_fuzzy' : dfz,
                        'doc_untranslated' : dun,
                        'doc_supportedness' : doc_supp,
                        'doc_percentages': doc_percentages,
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


def compare_languages(a, b):
    res = cmp(b['ui_supportedness'], a['ui_supportedness'])
    if not res:
        return cmp(a['name'], b['name'])
    else:
        return res

def compare_releases(a, b):
    res = cmp(a['firstlanguage'], b['firstlanguage'])
    if not res:
        return cmp(a['code'], b['code'])
    else:
        return res

def get_aggregate_stats(release, releasesfile = defaults.releases_xml):
    # Initialise modules
    modules = []

    dom = xml.dom.minidom.parse(releasesfile)
    releases = dom.getElementsByTagName("release")
    for myrelease in releases:
        releaseid = myrelease.getAttribute("id")
        if release and releaseid == release:
            module_tags = myrelease.getElementsByTagName("module")
            for module in module_tags:
                modid = module.getAttribute("id")
                branch = module.getAttribute("branch")
                if not branch: branch = "HEAD"
                modules.append((modid, branch))
            break

    stats = { }
    langs = teams.TranslationLanguages(show_hidden=1)
    for lang in langs:
        lname = langs[lang]
        stats[lang] = {
            'code' : lang,
            'name' : lname,
            'ui_translated' : 0,
            'ui_fuzzy' : 0,
            'ui_untranslated' : 0,
            'doc_translated' : 0,
            'doc_fuzzy' : 0,
            'doc_untranslated' : 0,
            'errors': [],
            }

    # Initialise POT sizes
    totalpot = 0; dtotalpot = 0
    for (modid, branch) in modules:
        res = Statistics.select(AND(Statistics.q.Module == modid,
                                    Statistics.q.Branch == branch,
                                    Statistics.q.Language == None))
        for stat in list(res):
            un = stat.Untranslated
            type = stat.Type
            if type=='ui': totalpot += un
            elif type=='doc': dtotalpot += un

    for (modid, branch) in modules:
        res = Statistics.select(AND(Statistics.q.Module == modid,
                                    Statistics.q.Branch == branch,
                                    Statistics.q.Language != None))
        for stat in list(res):
            type = stat.Type
            if type not in ['ui', 'doc']: continue

            lang = stat.Language
            if lang not in stats:
                stats[lang] = {
                    'code' : lang,
                    'name' : lang,
                    'ui_translated' : 0,
                    'ui_fuzzy' : 0,
                    'ui_untranslated' : 0,
                    'doc_translated' : 0,
                    'doc_fuzzy' : 0,
                    'doc_untranslated' : 0,
                    'errors': [('error' , "There is no translation team for '%s' in Gnome." % lang)],
                    }

            tr = stat.Translated
            fz = stat.Fuzzy

            stats[lang][type + '_translated'] += tr
            stats[lang][type + '_fuzzy'] += fz
            stats[lang][type + '_untranslated'] += un

    result = []
    if totalpot:
        for lang in stats:
            for type in ['ui', 'doc']:
                tr = stats[lang][type+'_translated']
                fz = stats[lang][type+'_fuzzy']
                if type=='ui':
                    fullsize = totalpot
                else:
                    fullsize = dtotalpot
                stats[lang][type+'_untranslated'] = fullsize - tr - fz
                un = stats[lang][type+'_untranslated']

                supp = 100*tr/fullsize
                perc = { 'translated' : supp,
                         'fuzzy' : 100*fz/fullsize,
                         'untranslated' : 100*un/fullsize }
                stats[lang][type+'_supportedness'] = supp
                stats[lang][type+'_percentages'] = perc
            result.append(stats[lang])

    result.sort(compare_languages)
    return result

            
    

    
            
    
    
    

if __name__=="__main__":
    import cgi
    import cgitb; cgitb.enable()
    from Cheetah.Template import Template

    print "Content-type: text/html; charset=UTF-8\n"

    releaseid = os.getenv("PATH_INFO")[1:]
    if releaseid:
        myrelease = Releases(only_release=releaseid, deep=0)
        if len(myrelease) and myrelease[0]['id'] == releaseid:
            html = Template(file="templates/release.tmpl")
            html.webroot = defaults.webroot
            html.release = myrelease[0]

            langs = teams.TranslationLanguages()
            status = get_aggregate_stats(releaseid)
            html.status = status
            print html
            print utils.TemplateInspector(html)
    else:
        t = Releases(deep=0)
        releases = t.data

        html = Template(file="templates/list-releases.tmpl")
        html.webroot = defaults.webroot
        html.releases = releases
        print html
        print utils.TemplateInspector(html)
    
