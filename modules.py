#!/usr/bin/env python

import defaults
import data

class XmlModules:
    
    def __init__(self, modfile = defaults.modules_xml, module = None):
        self.modules = data.getModules( only = module)
        only_module = module

        people = data.getPeople()

        for module in self.modules:
            modid = module

            if only_module and modid != only_module:
                continue
            #
            # maintainers = self.getMaintainers(module, default = defaults.maintainers)
            if self.modules[module].has_key('maintainer'):
                for maint in self.modules[module]['maintainer']:
                    if people.has_key(maint):
                        self.modules[module]['maintainer'][maint] = people[maint]

            if self.modules[module].has_key('branch'):
                for branch in self.modules[module]['branch']:
                    if not self.modules[module]["branch"][branch].has_key('domain'):
                        self.modules[module]["branch"][branch]['domain'] = {}
                    trdomains = self.modules[module]["branch"][branch]['domain'].keys()
                    if not self.modules[module]["branch"][branch].has_key('document'):
                        self.modules[module]["branch"][branch]['document'] = {}
                    documents = self.modules[module]["branch"][branch]['document'].keys()
                    for trdomain in trdomains:
                        here = self.modules[module]["branch"][branch]['domain'][trdomain]
                        if not here.has_key('potbase'):
                            here['potbase'] = self.modules[module]['id']
                        if not here.has_key('description'):
                            here['description'] = here['potbase']

                    for document in documents:
                        here = self.modules[module]["branch"][branch]['document'][document]
                        here['potbase'] = document
                        if not here.has_key('directory'):
                            here['directory'] = here['id']
                        if not here.has_key('description'):
                            here['description'] = here['id']


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
        branches = module["branch"].keys()
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
                    print >> sys.stderr, "Problem checking out module %s.%s" % (module["id"], branch)
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


class SvnModule:
    """Checks out a module from SVN if necessary to be able to work on it."""

    def __init__(self, module, real_update = 1):
        if not module: return None

        self.paths = {}
        self.module = module

        localroot = os.path.join(defaults.scratchdir, "svn")
        branches = module["branch"].keys()
        for branch in branches:
            moduledir = module["id"] + "." + branch
            checkoutpath = os.path.join(localroot, module["id"] + "." + branch)

            if real_update:
                if defaults.DEBUG:
                    print >>sys.stderr, "Checking '%s.%s' out to '%s'..." % (module["id"], branch, checkoutpath)
                co = self.checkout(module["svnroot"],
                                   module["svnmodule"], branch, 
                                   localroot,
                                   moduledir)

                if not co:
                    print >> sys.stderr, "Problem checking out module %s.%s" % (module["id"], branch)
                else:
                    self.paths[branch] = checkoutpath
            else:
                if os.access(checkoutpath, os.X_OK):
                    self.paths[branch] = checkoutpath


    def checkout(self, svnroot, module, branch, localroot, moduledir):

        import commands

        try: os.makedirs(localroot)
        except: pass

        if os.access(os.path.join(localroot, moduledir), os.X_OK | os.W_OK):
            command = "cd %(localdir)s && svn up --non-interactive" % {
                "localdir" : os.path.join(localroot, moduledir),
                }
        else:
            svnpath = svnroot + "/" + module
            if branch == "trunk" or branch == "HEAD":
                svnpath += "/trunk"
            else:
                svnpath += "/branches/" + branch
            command = "cd %(localroot)s && svn co --non-interactive %(svnpath)s %(dir)s" % {
                "localroot" : localroot,
                "svnpath" : svnpath,
                "dir" : moduledir,
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
    m = XmlModules()
    import pprint
    for modid in ['gnome-desktop']:
        #cvs = CvsModule(m[modid])
        print modid, ":\n", pprint.pprint(m[modid])
