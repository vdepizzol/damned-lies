#!/usr/bin/env python

import xml.dom.minidom
import defaults

class XmlModules:
    def getElementContents(self, node):
        nodelist = node.childNodes
        rc = ""
        for el in nodelist:
            if el.nodeType == el.TEXT_NODE:
                rc = rc + el.data
        return rc
        
    def getElementText(self, node, element, default = 0):
        all = node.getElementsByTagName(element)
        if not all or len(all)<1:
            return default

        rc = self.getElementContents(all[0])
        return rc

    def getElementList(self, node, element, subelement, default = 0):
        all = node.getElementsByTagName(element)
        if not all or len(all)<1:
            return default

        nodelist = all[0].getElementsByTagName(subelement)
        rc = []
        for el in nodelist:
            rc.append(self.getElementContents(el))
        return rc

    def getBranch(self, el, moduleid, cvsweb, cvsmodule, branch, default):
        if not branch: branch = "HEAD"

        trdomains = self.getTranslationDomains(el, default = defaults.translation_domains)
        documents = self.getDocuments(el, default = defaults.documents)
        regenerate = 1
        if el.hasAttribute("regenerate"):
            regenerate = int(el.getAttribute("regenerate"))
        for dom in trdomains:
            if not trdomains[dom]['potbase']:
                trdomains[dom]['potbase'] = moduleid
        for doc in documents:
            if not documents[doc]['potbase']:
                documents[doc]['potbase'] = moduleid

        rc = {
            "translation_domains" : trdomains,
            "documents" : documents,
            "regenerate" : regenerate,
            "cvsweb" : cvsweb % {'module' : cvsmodule, 'branch' : branch},
            }
        return rc

    def getBranches(self, module, moduleid, cvsweb, cvsmodule, default = 0):
        all = module.getElementsByTagName('branches')
        if not all or len(all)<1:
            rc = { }
            for branch in default:
                rc[branch] = self.getBranch(module, moduleid, cvsweb, cvsmodule, branch, default)
            return rc

        nodelist = all[0].getElementsByTagName('branch')
        rc = {}
        for el in nodelist:
            branch = el.getAttribute("tag")
            if not branch: branch = "HEAD"
            rc[branch] = self.getBranch(el, moduleid, cvsweb, cvsmodule, branch, default)
        return rc


    def getTranslationDomains(self, module, default = 0):
        all = module.getElementsByTagName("translation-domains")

        rc = {}
        for domain in default:
            rc[domain] = { "description": default[domain]["description"],
                           "potbase": default[domain]["potbase"] }

        if not all or len(all)<1:
            return rc

        nodelist = all[0].getElementsByTagName("domain")
        if not nodelist or len(nodelist)<1:
            return rc

        rc = {}
        for domain in nodelist:
            dir = self.getElementText(domain, "directory", "po")
            desc = self.getElementText(domain, "description", "UI translations")
            potname = domain.getAttribute("base")
            if not potname: potname = ""
            
            rc[dir] = { "description" : desc,
                        "potbase" : potname }
        return rc



    def getDocuments(self, module, default = 0):
        all = module.getElementsByTagName("documents")


        rc = {}
        for doc in default:
            rc[doc] = { "description": default[doc]["description"],
                        "potbase": default[doc]["potbase"] }

        if not all or len(all)<1:
            return rc

        nodelist = all[0].getElementsByTagName("document")
        if not nodelist or len(nodelist)<1:
            return rc

        rc = {}
        for doc in nodelist:
            if doc.hasAttribute("base"):
                base = doc.getAttribute("base")
            else:
                base = ""
            dir = self.getElementText(doc, "directory", "help")
            desc = self.getElementText(doc, "description", "User Guide")
            
            rc[dir] = { "description" : desc,
                        "potbase" : base }
        return rc

    def getBugzillaDetails(self, module, moduleid, default = 0):
        all = module.getElementsByTagName("bugzilla")
        if not all or len(all)<1:
            return  {
                "baseurl" : default["baseurl"],
                "xmlrpc" : default["xmlrpc"],
                "product" : moduleid,
                "component" : default["component"],
                }

        node = all[0]

        rc = {
           "baseurl" : self.getElementText(node, "baseurl", default["baseurl"]),
           "xmlrpc" : self.getElementText(node, "xmlrpc", default["xmlrpc"]),
           "product" : self.getElementText(node, "product", moduleid),
           "component" : self.getElementText(node, "component", default["component"]),
           }
        return rc

    def getMaintainers(self, module, default = 0):
        all = module.getElementsByTagName("maintainers")
        if not all or len(all)<1:
            return default

        nodelist = all[0].getElementsByTagName("maintainer")
        if not nodelist or len(nodelist)<1:
            return default

        rc = []
        for el in nodelist:
            maint = {
                "name" : self.getElementText(el, "name", ""),
                "email" : self.getElementText(el, "email", ""),
                "irc_nickname" : self.getElementText(el, "irc-nickname", ""),
                "webpage" : self.getElementText(el, "webpage", ""),
                }
                
            rc.append(maint)
        return rc

    
    def __init__(self, modfile = "gnome-modules.xml", module = None):
        self.modules = { }
        only_module = module

        dom = xml.dom.minidom.parse(modfile)
        
        mods = dom.getElementsByTagName("module")
        for module in mods:
            modid = module.getAttribute("id")

            if only_module and modid != only_module:
                continue
            description = self.getElementText(module, "description", default = modid)

            mycvsroot = self.getElementText(module, "cvs-root", default = defaults.cvsroot)
            mycvsweb = self.getElementText(module, "cvs-web", default = defaults.cvsweb)
            cvsmodule = self.getElementText(module, "cvs-module", default = modid)
            cvsbranch = self.getBranches(module, modid, mycvsweb, cvsmodule, default = defaults.cvsbranch )
            bugzilla = self.getBugzillaDetails(module, modid, default = defaults.bugzilla)
            maintainers = self.getMaintainers(module, default = defaults.maintainers)

            if not bugzilla['product']:
                bugzilla['product'] = modid

            self.modules[modid] = {
                "id" : modid,
                "description" : description,
                "cvsroot" : mycvsroot,
                "cvsweb" : mycvsweb,
                "cvsmodule"  : cvsmodule,
                "cvsbranches" : cvsbranch,
                "bugzilla" : bugzilla,
                "maintainers" : maintainers,
                }


    # Implement dictionary methods
    def __getitem__(self, key): return self.modules[key]

    def __setitem__(self, key, value): self.modules[key] = value

    def __len__(self): return len(self.modules)

    def keys(self): return self.modules.keys()

    def items(self): return self.modules.items()  

    def values(self): return self.modules.values()

    def __iter__(self): return self.modules.__iter__()



import os.path, sys

class CvsModule:
    """Checks out a module from CVS if necessary to be able to work on it."""

    def __init__(self, module, real_update = 1):
        if not module: return None

        self.paths = {}
        self.module = module

        localroot = os.path.join(defaults.scratchdir, "cvs")
        branches = module["cvsbranches"]
        for branch in branches:
            moduledir = module["id"] + "." + branch
            checkoutpath = os.path.join(localroot, module["id"] + "." + branch)

            if real_update:
                if defaults.DEBUG:
                    print >>sys.stderr, "Checking '%s.%s' out to '%s'..." % (module["id"], branch, checkoutpath)
                co = self.checkout(module["cvsroot"],
                                   module["cvsmodule"], branch, 
                                   localroot,
                                   moduledir)

                if not co:
                    print >> sys.stderr, "Problem with checking out module %s.%s" % (module["id"], branch)
                else:
                    self.paths[branch] = checkoutpath
            else:
                if os.access(checkoutpath, os.X_OK):
                    self.paths[branch] = checkoutpath


    def checkout(self, cvsroot, module, branch, localroot, moduledir):

        import commands

        try: os.makedirs(localroot)
        except: pass

        try:
            os.stat(os.path.join(localroot, moduledir))
            command = "cd %(localdir)s && cvs -z4 up -Pd" % {
                "localdir" : os.path.join(localroot, moduledir),
                }
        except OSError:
            command = "cd %(localroot)s && cvs -d%(cvsroot)s -z4 co -d%(dir)s -r%(branch)s %(module)s" % {
                "localroot" : localroot,
                "cvsroot" : cvsroot,
                "dir" : moduledir,
                "branch" : branch,
                "module" : module,
                }
            

        if defaults.DEBUG:
            print >>sys.stderr, command
        (error, output) = commands.getstatusoutput(command)
        if not error:
            if defaults.DEBUG:
                print >> sys.stderr, output
            return 1
        else:
            if defaults.DEBUG:
                print >> sys.stderr, output
            return 0


if __name__=="__main__":
    m = XmlModules("gnome-modules.xml")
    for modid in m:
        #cvs = CvsModule(m[modid])
        print modid, ":\n", m[modid]
