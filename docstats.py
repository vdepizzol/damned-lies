#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2005 Danilo Segan <danilo@gnome.org>.
#
# This file is part of doc-l10n-status.
#
# doc-l10n-status is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# doc-l10n-status is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with doc-l10n-status; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from l10n_config import *


# Configuration done, no need to change anything below

import os, os.path, sys, commands

def read_makefile_variable(file, variable):
    import re
    fin = open(file, "r")
    
    fullline = ""
    for line in fin:
        fullline += " " + line.strip()
        if len(line)>2 and line[-2] == "\\":
            fullline = fullline[:-2]
        else:
            match = re.match(variable + r"\s*=\s*([^=]*)", fullline.strip())
            if match:
                return match.group(1)
            else:
                # FIXME: hackish, works for www.gnome.org/tour
                match = re.match("include\s+(.+)", fullline.strip())
                if match:
                    import os.path
                    incfile = os.path.join(os.path.dirname(file), os.path.basename(match.group(1)))
                    if incfile.find("gnome-doc-utils.make")==-1:
                        print >>sys.stderr, "Reading file %s..." % (incfile)
                        var = read_makefile_variable(incfile, variable)
                        if var != "":
                            return var
                    
            fullline = ""
    return ""

def doc_stats_for_module(module, checkoutdir, docpath, out_dir, out_domain):
    sourcedir = os.path.join(checkoutdir, docpath)
    moduleid = module["id"]

    errors = []

    if not os.path.isdir(sourcedir):
        errors.append(("error", "Can't find checkout directory."))
        return { 'errors' : errors }

    # now read interesting variables from the Makefile.am
    makefileam = os.path.join(module["localpath"], "Makefile.am")
    modulename = read_makefile_variable(makefileam, "DOC_MODULE")
    includes = read_makefile_variable(makefileam, "DOC_INCLUDES")
    entitites = read_makefile_variable(makefileam, "DOC_ENTITIES")
    languages = read_makefile_variable(makefileam, "DOC_LINGUAS")

    # Generate POT file
    potname = out_domain + ".pot"
    try: os.makedirs(out_dir)
    except: pass

    # Use two different files so we can introduce diff's if we wish here too
    fullpot = os.path.join(sourcedir, "C", potname)
    newpot = os.path.join(out_dir, potname)
    fullpot = newpot # FIXME: add diff'ing capability
    
    if not modulename:
        errors.append(("error", "Module %s doesn't look like gnome-doc-utils module." % (moduleid)))
        return { 'errors' : errors }

    if not os.access(os.path.join(sourcedir, "C", modulename + ".xml"), os.R_OK):
        if os.access(os.path.join(sourcedir, "C", moduleid + ".xml"), os.R_OK):
            errors.append(("warn", "DOC_MODULE doesn't resolve to a real file, using '%s.xml'." % (moduleid)))
            modulename = moduleid
        else:
            errors.append(("error", "DOC_MODULE doesn't point to a real file, probably a macro."))
            return { 'errors' : errors }

    files = [ modulename + ".xml" ]

    # Add DOC_INCLUDES to files list
    for file in includes.split(" "):
        if file.strip() != "":
            files.append(file.strip())

    allfiles = ""
    for file in files:
        allfiles += " " + os.path.join("C", file)
    command = "cd %s && xml2po -o %s -e %s" % (sourcedir, fullpot, allfiles)

    if defaults.DEBUG: print >>sys.stderr, command
    (error, output) = commands.getstatusoutput(command)
    if error:
        errors.append(("error", "Error regenerating POT file for module %s" % (out_domain)))
    if defaults.DEBUG: print >> sys.stderr, output

    potstats = self.po_file_stats("LC_ALL=C LANG=C LANGUAGE=C msgfmt --statistics -o /dev/null %s" % (fullpot))
    potstats['errors'].extend(errors)

    for lang in languages.split(" "):
        print >>sys.stderr, "Processing %s..." % (lang)
        if lang.strip() != "":
            lang = lang.strip()
            poname = out_domain + "." + lang + ".po"
            fullpo = os.path.join(potdir, poname)
            pofile = os.path.join(sourcedir, lang, lang + ".po")
            command = "msgmerge -o %s %s %s" % (fullpo, pofile, fullpot)
            command = "%s %s %s > %s" % (POMERGE, pofile, fullpot, fullpo)
            (error, output) = commands.getstatusoutput(command)
            print >> sys.stderr, output
            if not error:
                (translated, fuzzy, untranslated) = pofile_statistics("LC_ALL=C LANG=C LANGUAGE=C msgfmt --statistics -o /dev/null %s" % (fullpo))

                if not modstats.has_key(moduleid): modstats[moduleid] = { }
                if not langstats.has_key(lang): langstats[lang] = { }
                modstats[moduleid][lang] = {
                    "poname" : poname,
                    "cvsdir" : module["cvsdir"],
                    "branch" : module["cvsbranch"],
                    "translated" : translated,
                    "untranslated" : untranslated,
                    "fuzzy" : fuzzy,
                    }
                langstats[lang][moduleid] = {
                    "poname" : poname,
                    "cvsdir" : module["cvsdir"],
                    "branch" : module["cvsbranch"],
                    "translated" : translated,
                    "untranslated" : untranslated,
                    "fuzzy" : fuzzy,
                    }
