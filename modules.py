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

class ScmModule:
    """Checks out a module from CVS/SVN/HG/GIT if necessary to be able to work on it."""
    
    def __init__(self, module, real_update = 1):
        if not module: return None

        self.paths = {}
        self.module = module
        self.type = module["scmroot"]["type"]
        if self.type not in ('cvs','svn','hg','git', 'bzr'):
            raise Exception("Source code manager of type '%s' non supported." % self.type)
        
        if real_update:
            branches = module["branch"].keys()
            for branch in branches:
                co = self.checkout(branch)
    
    def get_branches(self):
        return self.module["branch"].keys()
    
    def checkout(self, branch):
        """Checks out a specific branch of the module."""
        
        import os, commands
        
        module = self.module["scmmodule"]
        localroot = os.path.join(defaults.scratchdir, self.type)
        moduledir = self.module["id"] + "." + branch
        modulepath = os.path.join(localroot, moduledir)
        scmroot = self.module["scmroot"]["path"]

        try: os.makedirs(localroot)
        except: pass
        
        commandList = []
        if os.access(modulepath, os.X_OK | os.W_OK):
            # Path exists, update repos
            if self.type == "cvs":
                commandList.append("cd \"%(localdir)s\" && cvs -z4 up -Pd" % {
                    "localdir" : modulepath,
                    })
            elif self.type == "svn":
                commandList.append("cd \"%(localdir)s\" && svn up --non-interactive" % {
                    "localdir" : modulepath,
                    })
            elif self.type == "hg":
                commandList.append("cd \"%(localdir)s\" && hg revert --all" % {
                    "localdir" : modulepath,
                    })
            elif self.type == "git":
                commandList.append("cd \"%(localdir)s\" && git checkout %(branch)s && git reset --hard && git clean -d" % {
                    "localdir" : modulepath,
                    "branch" : branch,
                    })
            elif self.type == "bzr":
                commandList.append("cd \"%(localdir)s\" && bzr up" % {
                    "localdir" : modulepath,
                    })
        else:
            # Checkout
            if self.type == "cvs":
                commandList.append("cd \"%(localroot)s\" && cvs -d%(cvsroot)s -z4 co -d%(dir)s -r%(branch)s %(module)s" % {
                "localroot" : localroot,
                "cvsroot" : scmroot,
                "dir" : moduledir,
                "branch" : branch,
                "module" : module,
                })
            elif self.type == "svn":
                svnpath = scmroot + "/" + module
                if branch == "trunk" or branch == "HEAD":
                    svnpath += "/trunk"
                else:
                    svnpath += "/branches/" + branch
                if self.module["branch"][branch].has_key("subpath"):
                    svnpath += "/%s" % self.module["branch"][branch]["subpath"]
                commandList.append("cd \"%(localroot)s\" && svn co --non-interactive %(svnpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "svnpath" : svnpath,
                    "dir" : moduledir,
                    })
            elif self.type == "hg":
                hgpath = scmroot + "/" + module
                commandList.append("cd \"%(localroot)s\" && hg clone %(hgpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "hgpath" : hgpath,
                    "dir" : moduledir,
                    })
                commandList.append("cd \"%(localdir)s\" && hg update %(branch)s" % {
                    "localdir" : modulepath,
                    "branch" : branch,
                    })
            elif self.type == "git":
                gitpath = scmroot + "/" + module
                commandList.append("cd \"%(localroot)s\" && git clone %(gitpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "gitpath" : gitpath,
                    "dir" : moduledir,
                    })
                commandList.append("cd \"%(localdir)s\" && git checkout %(branch)s" % {
                    "localdir" : modulepath,
                    "branch" : branch,
                    })
            elif self.type == "bzr":
                bzrpath = scmroot + "/" + module
                if branch == "trunk" or branch == "HEAD":
                    bzrpath += "/trunk"
                else:
                    bzrpath += "/branches/" + branch
                if self.module["branch"][branch].has_key("subpath"):
                    bzrpath += "/%s" % self.module["branch"][branch]["subpath"]
                commandList.append("cd \"%(localroot)s\" && bzr co --lightweight %(bzrpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "bzrpath" : bzrpath,
                    "dir" : moduledir,
                    })
        
        # Run command(s)
        errorsOccured = 0
        if defaults.DEBUG:
            print >>sys.stdout, "Checking '%s.%s' out to '%s'..." % (module, branch, modulepath)
        for command in commandList:
            if defaults.DEBUG:
                print >>sys.stdout, command
            (error, output) = commands.getstatusoutput(command)
            if defaults.DEBUG:
                print >> sys.stderr, output
            if error:
                errorsOccured = 1
                if defaults.DEBUG:
                    print >> sys.stderr, error
        if errorsOccured:
            print >> sys.stderr, "Problem checking out module %s.%s" % (module, branch)
            return 0
        else:
            self.paths[branch] = modulepath
            return 1


if __name__=="__main__":
    m = XmlModules()
    import pprint
    for modid in ['gnome-desktop']:
        print modid, ":\n", pprint.pprint(m[modid])
