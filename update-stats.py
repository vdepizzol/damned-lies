#!/usr/bin/env python

import defaults

import database
import modules
import teams

import potdiff

import os, sys, commands, datetime

class LocStatistics:
    """Generate all statistics for provided module and source code path."""

    def update_pot_errors_in_db(self, module, branch, type, domain, errors):
        old = database.Statistics.select(database.AND(database.Statistics.q.Module == module,
                                                      database.Statistics.q.Domain == domain,
                                                      database.Statistics.q.Branch == branch,
                                                      database.Statistics.q.Language == None,
                                                      database.Statistics.q.Type == type))

        for oldS in old:
            for msg in oldS.Messages:
                database.Information.delete(msg.id)

            for (msgtype, message) in errors:
                NewInfo = database.Information(Statistics = oldS,
                                               Type = msgtype,
                                               Description = message)

    def update_stats_database(self, module, branch, type, domain, date, language, translated, fuzzy, untranslated, errors):
        MyArchive = database.ArchivedStatistics(Module = module,
                                                Branch = branch,
                                                Type = type,
                                                Domain = domain,
                                                Date = date,
                                                Language = language,
                                                Translated = translated,
                                                Fuzzy = fuzzy,
                                                Untranslated = untranslated)
        if language:
            old = database.Statistics.selectBy(Module = module,
                                               Branch = branch,
                                               Type = type,
                                               Domain = domain,
                                               Language = language)
        else:
            old = database.Statistics.select(database.AND(database.Statistics.q.Module == module,
                                                          database.Statistics.q.Domain == domain,
                                                          database.Statistics.q.Branch == branch,
                                                          database.Statistics.q.Language == None,
                                                          database.Statistics.q.Type == type))

        for oldS in old:
            for msg in oldS.Messages:
                database.Information.delete(msg.id)
            database.Statistics.delete(oldS.id)

        MyStat = database.Statistics(Module = module,
                                     Branch = branch,
                                     Type = type,
                                     Domain = domain,
                                     Date = date,
                                     Language = language,
                                     Translated = translated,
                                     Fuzzy = fuzzy,
                                     Untranslated = untranslated)

        for (msgtype, message) in errors:
            NewArchiveInfo = database.ArchivedInformation(Statistics = MyArchive,
                                                          Type = msgtype,
                                                          Description = message)
            NewInfo = database.Information(Statistics = MyStat,
                                           Type = msgtype,
                                           Description = message)
        

        

    def __init__(self, module, onlybranch = None):
        self.module = module
        if module.has_key('svnroot'):
            COs = modules.SvnModule(module, 1)
        elif module.has_key('cvsroot'):
            COs = modules.CvsModule(module, 1)
        else:
            raise Exception("Can't fetch source code for this module.")

        mybranches = COs.paths.keys()
        if onlybranch and onlybranch in mybranches:
            mybranches = [onlybranch]
        
        for branch in mybranches:
            if module["branch"][branch].has_key('regenerate') and not module["branch"][branch]["regenerate"]:
                continue

            if module["branch"][branch].has_key("stringfrozen") and module["branch"][branch]["stringfrozen"]:
                self.STRINGFREEZE = 1
            else:
                self.STRINGFREEZE = 0

            for podir in module["branch"][branch]["domain"]:
                potbase = module["branch"][branch]["domain"][podir]['potbase']

                self.podir = podir
                self.potbase = potbase
                self.branch = branch
                
                outputdir = os.path.join(defaults.potdir, module["id"] + "." + branch)
                outputdomain = potbase + "." + branch
                
                if not os.path.isdir(outputdir):
                    os.makedirs(outputdir)

                if defaults.DEBUG: print >>sys.stderr, "%s.%s/%s" % (module["id"],branch,podir)
                self.ui_l10n_stats(COs.paths[branch], podir, potbase, outputdir, outputdomain)

            if defaults.DEBUG: print >>sys.stderr, "DOCUMENTS: ", module["branch"][branch]["document"]
            for doc in module["branch"][branch]["document"]:
                potbase = module["branch"][branch]["document"][doc]['potbase']
                docsubdir = module["branch"][branch]["document"][doc]['directory']

                outputdir = os.path.join(defaults.potdir, module["id"] + "." + branch, "docs")

                ret = self.doc_l10n_stats(COs.paths[branch], docsubdir, potbase, outputdir)
                if len(ret['errors']):
                    self.update_pot_errors_in_db(module['id'], branch, 'document', potbase, ret['errors'])



    def notify_list(self, out_domain, diff):
        """Send notification about string changes described in diff.

        Uses defaults.notifications_to as "to" address,
        defaults.WHOAREWE as "from" address, and sends
        using SMTP on localhost:25."""
        import smtplib
        from email.MIMEText import MIMEText
        text = """This is an automatic notification from status generation scripts on:
    %(ourweb)s.

There have been following string additions to module '%(module)s':

    %(potdiff)s

Note that this doesn't directly indicate a string freeze break, but it
might be worth investigating.
""" % { 'module' : out_domain,
        'ourweb' : defaults.WHEREAREWE,
        'potdiff' : "\n    ".join(diff) }
        
        msg = MIMEText(text)
        msg['Subject'] = "String additions to '%s'" % (out_domain)
        msg['From'] = "Gnome Status Pages <%s>" % (defaults.WHOAREWE)
        msg['To'] = defaults.notifications_to

        s = smtplib.SMTP()
        s.connect()
        s.sendmail(defaults.WHOAREWE, defaults.notifications_to, msg.as_string())
        s.close()

        
    def ui_l10n_stats(self, base_dir, po_dir, pot_base, out_dir, out_domain):
        """Generates translation status for UI elements and updates the database."""
        
        popath = os.path.join(base_dir, po_dir)

        # Run intltool-update -m to check for some errors
        errors = self.check_pot_regeneration(popath)

        # Generate PO template (POT) file
        command = "cd %(dir)s && intltool-update -g '%(domain)s' -p" % {
            "dir" : popath,
            "domain" : pot_base,
            }
        if defaults.DEBUG: print >>sys.stderr, command
        (error, output) = commands.getstatusoutput(command)
        if defaults.DEBUG: print >> sys.stderr, output

        potfile = os.path.join(popath, pot_base + ".pot")
        newpot = os.path.join(out_dir, out_domain + ".pot")
        NOW = datetime.datetime.now()

        if error or not os.access(potfile, os.R_OK):
            if defaults.DEBUG: print >> sys.stderr, "Can't generate POT file for %s/%s." % (self.module["id"], po_dir)
            errors.append(("error", "Can't generate POT file."))
            pot_stats = self.po_file_stats(potfile, 0)
            pot_stats['errors'].extend(errors)
            self.update_stats_database(module = self.module["id"], branch = self.branch, type = 'ui',
                                       domain = self.podir, date = NOW, language = None,
                                       translated = 0, fuzzy = 0, untranslated = int(pot_stats['untranslated']),
                                       errors = pot_stats['errors'])
            return {'translated': 0, 'fuzzy': 0, 'untranslated': int(pot_stats['untranslated']), 'errors': errors}

        # whether pot has changed
        potchanged = 1

        # If old pot already exists and we are in string freeze
        if os.access(newpot, os.R_OK):
            if self.STRINGFREEZE:
                diff = potdiff.diff(newpot, potfile, 1)
                if len(diff):
                    self.notify_list(out_domain, diff)

            # If old pot already exists, lets see if it has changed at all
            diff = potdiff.diff(newpot, potfile)
            if len(diff) == 0:
                potchanged = 0


        pot_stats = self.po_file_stats(potfile, 0)
        pot_stats['errors'].extend(errors)

        if not self.copy_file(potfile, newpot):
            pot_stats['errors'].append(('error', "Can't copy new POT file to public location."))

        postats = self.update_po_files(base_dir, popath, potfile, out_dir, out_domain, potchanged)

        self.update_stats_database(module = self.module["id"], branch = self.branch, type = 'ui',
                                   domain = self.podir, date = NOW, language = None,
                                   translated = 0, fuzzy = 0, untranslated = int(pot_stats['untranslated']),
                                   errors = pot_stats['errors'])

        for lang in postats:
            langs = teams.TranslationLanguages(show_hidden=1)
            if not lang or not langs.has_key(lang):
                postats[lang]['errors'].append(("warn", "There is no translation team in charge of '%s' translation." % (lang)))

            self.update_stats_database(module = self.module["id"], branch = self.branch, type = 'ui',
                                       domain = self.podir, date = NOW, language = lang,
                                       translated = int(postats[lang]['translated']),
                                       fuzzy = int(postats[lang]['fuzzy']),
                                       untranslated = int(postats[lang]['untranslated']),
                                       errors = postats[lang]['errors'])

        return pot_stats


    def update_po_files(self, module_path, po_path, pot_file, out_dir, out_domain, potchanged):
        if defaults.fuzzy_matching:
            command = "msgmerge -o %(outpo)s %(pofile)s %(potfile)s"
        else:
            command = "msgmerge -N -o %(outpo)s %(pofile)s %(potfile)s"

        stats = {}

        for file in os.listdir(po_path):
            if file[-3:] == ".po":
                lang = file[:-3]

                outpo = os.path.join(out_dir, out_domain + "." + lang + ".po")

                srcpo = os.path.join(po_path, file)
                if not potchanged and os.access(outpo,os.R_OK) and os.stat(srcpo)[8] < os.stat(outpo)[8]:
                    continue
                    
                realcmd = command % {
                    'outpo' : outpo,
                    'pofile' : srcpo,
                    'potfile' : pot_file,
                    }
                if defaults.DEBUG: print >>sys.stderr, realcmd
                (error, output) = commands.getstatusoutput(realcmd)
                if defaults.DEBUG: print >> sys.stderr, output

                langstats = self.po_file_stats(outpo, 1)
                langstats['errors'].extend(self.check_lang_support(module_path, po_path, lang))

                stats[lang] = langstats
                if defaults.DEBUG: print >>sys.stderr, lang + ":\n" + str(langstats)
        return stats
                                             
                

    def check_lang_support(self, module_path, po_path, lang):
        "Checks if language is listed in one of po/LINGUAS, configure.ac or configure.in"

        LINGUAShere = os.path.join(po_path, "LINGUAS")
        LINGUASpo = os.path.join(module_path, "po", "LINGUAS") # if we're in eg. po-locations/
        configureac = os.path.join(module_path, "configure.ac")
        configurein = os.path.join(module_path, "configure.in")

        errors = []

        # is "lang" listed in either of po/LINGUAS, ./configure.ac(ALL_LINGUAS) or ./configure.in(ALL_LINGUAS)
        in_config = 0
        for LINGUAS in [LINGUAShere, LINGUASpo]:
            if os.access(LINGUAS, os.R_OK):
                lfile = open(LINGUAS, "r")
                for line in lfile:
                    line = line.strip()
                    if len(line) and line[0]=="#": continue
                    if lang in line.split(" "):
                        if defaults.DEBUG: print >>sys.stderr, "Language '%s' found in LINGUAS." % (lang)
                        in_config = 1
                        break
                lfile.close()
                if not in_config:
                    errors.append(("warn", "Entry for this language is not present in LINGUAS file."))
                return errors
        
        import re
        for configure in [configureac, configurein]:
            if not in_config and os.access(configure, os.R_OK):
                cfile = open(configure, "r")
                lines = []
                prev = ""
                for line in cfile:
                    line = prev + line.strip()
                    if line.count('"') % 2 == 1:
                        prev = line
                    else:
                        lines.append(line)
                        prev = ""
                    
                for line in lines:
                    line = line.strip()
                    test = re.match('ALL_LINGUAS\s*=\s*"([^"]*)"', line)
                    if test:
                        value = test.groups(1)[0]
                        if lang in value.split(" "):
                            if defaults.DEBUG: print >>sys.stderr, "Language '%s' found in %s." % (lang, configure)
                            in_config = 1
                        break
                cfile.close()
                if not in_config:
                    errors.append(("warn", "Entry for this language is not present in ALL_LINGUAS in configure file."))
                return errors
                
        errors.append(("warn", "Don't know where to look if this language is actually used, ask the module maintainer."))
        return errors

    def check_pot_regeneration(self, po_path):
        """Check if there were any problems regenerating a POT file."""
        errors = []

        command = "cd %(dir)s && rm -f missing notexist && intltool-update -m" % { "dir" : po_path, }
        if defaults.DEBUG: print >>sys.stderr, command
        (error, output) = commands.getstatusoutput(command)
        if defaults.DEBUG: print >> sys.stderr, output

        if error:
            if defaults.DEBUG: print >> sys.stderr, "Error running 'intltool-update -m' check."
            errors.append( ("error", "Errors while running 'intltool-update -m' check.") )

        missing = os.path.join(po_path, "missing")
        if os.access(missing, os.R_OK):
            f = open(missing, "r")
            errors.append( ("warn",
                            "There are some missing files from POTFILES.in: <ul><li>"
                            + "</li>\n<li>".join(f.readlines())
                            + "</li>\n</ul>") )
            
        notexist = os.path.join(po_path, "notexist")
        if os.access(notexist, os.R_OK):
            f = open(notexist, "r")
            errors.append(("error",
                           "Following files are referenced in either POTFILES.in or POTFILES.skip, yet they don't exist: <ul><li>"
                           + "</li>\n<li>".join(f.readlines())
                           + "</li>\n</ul>"))
        return errors

                   


    def po_file_stats(self, pofile, msgfmt_checks = 1):

        errors = []

        try: os.stat(pofile)
        except OSError: errors.append(("error", "PO file '%s' doesn't exist." % pofile))

        if msgfmt_checks:
            command = "LC_ALL=C LANG=C LANGUAGE=C msgfmt -cv -o /dev/null %s" % pofile
        else:
            command = "LC_ALL=C LANG=C LANGUAGE=C msgfmt --statistics -o /dev/null %s" % pofile

        if defaults.DEBUG: print >>sys.stderr, command
        (error, output) = commands.getstatusoutput(command)
        if defaults.DEBUG: print >>sys.stderr, output

        if error:
            if msgfmt_checks:
                errors.append(("error", "PO file '%s' doesn't pass msgfmt check: not updating." % (pofile)))
            else:
                errors.append(("error", "Can't get statistics for POT file '%s'." % (pofile)))

        import re
        r_tr = re.search(r"([0-9]+) translated", output)
        r_un = re.search(r"([0-9]+) untranslated", output)
        r_fz = re.search(r"([0-9]+) fuzzy", output)

        if r_tr: translated = r_tr.group(1)
        else: translated = 0
        if r_un: untranslated = r_un.group(1)
        else: untranslated = 0
        if r_fz: fuzzy = r_fz.group(1)
        else: fuzzy = 0

        if msgfmt_checks:
            # Lets check if PO files are in UTF-8
            command = ("LC_ALL=C LANG=C LANGUAGE=C " +
                       "msgconv -t UTF-8 %s |" +
                       "diff -u %s - >/dev/null") % (pofile,
                                                     pofile)
            if defaults.DEBUG: print >>sys.stderr, command
            (error, output) = commands.getstatusoutput(command)
            if defaults.DEBUG: print >>sys.stderr, output
            if error:
                errors.append(("warn",
                               "PO file '%s' is not UTF-8 encoded." % (pofile)))
        return {
            'translated' : translated,
            'fuzzy' : fuzzy,
            'untranslated' : untranslated,
            'errors' : errors,
            }

    def copy_file(self, file1, file2):
        try:
            fin = open(file1, "rb")
            fout = open(file2, "wb")

            block = fin.read(16*1024)
            while block:
                fout.write(block)
                block = fin.read(16*1024)
            fout.close()
            fin.close()

            if os.access(file2, os.R_OK):
                return 1
            else:
                return 0
        except:
            return 0


    def read_makefile_variable(self, file, variable):
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
                            var = self.read_makefile_variable(incfile, variable)
                            if var != "":
                                return var

                fullline = ""
        return ""

    def doc_l10n_stats(self, checkoutdir, docpath, potbase, out_dir):
        if defaults.DEBUG:
            print >>sys.stderr, "doc_l10n_stats(%s, %s, %s, %s)" % (checkoutdir,
                                                                    docpath,
                                                                    potbase,
                                                                    out_dir)
        sourcedir = os.path.join(checkoutdir, docpath)
        module = self.module
        moduleid = module["id"]

        errors = []

        if not os.path.isdir(sourcedir):
            errors.append(("error", "Can't find checkout directory."))
            return { 'errors' : errors, 'translated' : 0, 'untranslated' : 0, 'fuzzy' : 0 }

        # read interesting variables from the Makefile.am
        makefileam = os.path.join(sourcedir, "Makefile.am")
        try:
            modulename = self.read_makefile_variable(makefileam, "DOC_MODULE")
            includes = self.read_makefile_variable(makefileam, "DOC_INCLUDES")
            entitites = self.read_makefile_variable(makefileam, "DOC_ENTITIES")
            figures = self.read_makefile_variable(makefileam, "DOC_FIGURES")
            languages = self.read_makefile_variable(makefileam, "DOC_LINGUAS")
        except IOError:
            # probably file not found or unreadable
            modulename = None

        # Generate POT file
        try: os.makedirs(out_dir)
        except: pass

        if not modulename:
            errors.append(("error", "Module %s doesn't look like gnome-doc-utils module." % (moduleid)))
            return { 'errors' : errors, 'translated' : 0, 'untranslated' : 0, 'fuzzy' : 0 }

        if not os.access(os.path.join(sourcedir, "C", modulename + ".xml"), os.R_OK):
            if os.access(os.path.join(sourcedir, "C", moduleid + ".xml"), os.R_OK):
                errors.append(("warn", "DOC_MODULE doesn't resolve to a real file, using '%s.xml'." % (moduleid)))
                modulename = moduleid
            else:
                errors.append(("error", "DOC_MODULE doesn't point to a real file, probably a macro."))
                return { 'errors' : errors, 'translated' : 0, 'untranslated' : 0, 'fuzzy' : 0 }

        out_domain = potbase + "." + self.branch

        # Use two different files so we can introduce diff's if we wish here too
        potname = out_domain + ".pot"
        fullpot = os.path.join(sourcedir, "C", potname)
        newpot = os.path.join(out_dir, potname)
        
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
            errors.append(("error",
                           "Error regenerating POT file for document %s:\n<pre>%s\n%s</pre>" % (out_domain,
                                                                                                command,
                                                                                                output)))
        if defaults.DEBUG: print >> sys.stderr, output

        pot_stats = self.po_file_stats(fullpot,0)
        pot_stats['errors'].extend(errors)

        # If old pot already exists, lets take note of it's mtime

        potchanged = 1
        if os.access(newpot, os.R_OK):
            # If old pot already exists, lets see if it has changed at all
            diff = potdiff.diff(newpot, fullpot)
            if len(diff) == 0:
                potchanged = 0

        self.copy_file(fullpot, newpot)

        NOW = datetime.datetime.now()
        self.update_stats_database(module = self.module["id"], branch = self.branch, type = 'doc',
                                   domain = docpath, date = NOW, language = None,
                                   translated = 0, fuzzy = 0, untranslated = int(pot_stats['untranslated']),
                                   errors = pot_stats['errors'])

        postats = self.update_doc_po_files(sourcedir, fullpot, out_dir, out_domain, languages, potchanged, potbase, docpath)

        langs = teams.TranslationLanguages()
        for lang in postats:
            if lang and not langs.has_key(lang):
                postats[lang]['errors'].append(("error", "There is no translation team in charge of %s." % (lang)))

            self.update_stats_database(module = self.module["id"], branch = self.branch, type = 'doc',
                                       domain = docpath, date = NOW, language = lang,
                                       translated = int(postats[lang]['translated']),
                                       fuzzy = int(postats[lang]['fuzzy']),
                                       untranslated = int(postats[lang]['untranslated']),
                                       errors = postats[lang]['errors'])


        return pot_stats


    def update_doc_po_files(self, docdir, pot_file, out_dir, out_domain, languages, potchanged = 1, potbase = None, docpath = None):
        if defaults.fuzzy_matching:
            command = "msgmerge -o %(outpo)s %(pofile)s %(potfile)s"
        else:
            command = "msgmerge -N -o %(outpo)s %(pofile)s %(potfile)s"

        stats = {}

        for file in os.listdir(docdir):
            if os.path.isdir(os.path.join(docdir, file)) and os.path.isfile(os.path.join(docdir, file,file+".po")):
                myfile = os.path.join(docdir, file,file+".po")
                lang = file

                outpo = os.path.join(out_dir, out_domain + "." + lang + ".po")
                if not potchanged and os.access(outpo, os.R_OK) and os.stat(myfile)[8] < os.stat(outpo)[8]:
                    continue

                realcmd = command % {
                    'outpo' : outpo,
                    'pofile' : myfile,
                    'potfile' : pot_file,
                    }
                if defaults.DEBUG: print >>sys.stderr, realcmd
                (error, output) = commands.getstatusoutput(realcmd)
                if defaults.DEBUG: print >> sys.stderr, output

                langstats = self.po_file_stats(outpo, 1)
                if lang not in languages:
                    langstats['errors'].append(("warn", "DOC_LINGUAS list doesn't include this language."))

                stats[lang] = langstats
                if defaults.DEBUG: print >>sys.stderr, lang + ":\n" + str(langstats)

                if defaults.generate_docs:
                    self.generate_translated_docs(docdir, potbase, lang, outpo,
                                                  os.path.join(defaults.scratchdir, "xml", self.module["id"] + "." + self.branch,
                                                               docpath))
        return stats

    def generate_translated_docs(self, sourcedir, docbase, lang, pofile, out_dir):
        """Generates translated XML documentation using xml2po.

        sourcedir: base directory for the document (one containing Makefile.am with DOC_MODULE).
        docbase: base name for the document file, i.e. DOC_MODULE value.
        lang: language for which we are merging.
        pofile: PO file with translation to merge.
        out_dir: directory where to output translation.
        """
        # read interesting variables from the Makefile.am
        makefileam = os.path.join(sourcedir, "Makefile.am")
        modulename = self.read_makefile_variable(makefileam, "DOC_MODULE")
        includes = self.read_makefile_variable(makefileam, "DOC_INCLUDES")
        entitites = self.read_makefile_variable(makefileam, "DOC_ENTITIES")
        figures = self.read_makefile_variable(makefileam, "DOC_FIGURES")
        languages = self.read_makefile_variable(makefileam, "DOC_LINGUAS")

        try: os.makedirs(os.path.join(out_dir, lang))
        except: pass

        # Copy figures over
        if not figures:
            allfigs = []
            for file in os.listdir(os.path.join(sourcedir,"C","figures")):
                if file[-4:]==".png":
                    allfigs.append(os.path.join("figures", file))
        else:
            allfigs = figures.split()

        for fig in allfigs:
            newfigpath = os.path.join(out_dir, lang, fig)
            figdir = os.path.dirname(newfigpath)
            try: os.makedirs(figdir)
            except: pass
            if not self.copy_file(os.path.join(sourcedir, lang, fig), newfigpath):
                # Fallback to untranslated figures
                self.copy_file(os.path.join(sourcedir, "C", fig), newfigpath)

        # Generate XML files
        if not modulename: modulename = docbase
        files = [ modulename + ".xml" ]
        for file in includes.split():
            files.append(file)

        for file in files:
            command = "cd %(sourcedir)s && xml2po -e -l %(lang)s -p %(pofile)s -o %(outfile)s %(infile)s" % {
                'sourcedir' : sourcedir,
                'pofile' : pofile,
                'outfile' : os.path.join(os.path.join(out_dir, lang, file)),
                'infile' : os.path.join(os.path.join(sourcedir, "C", file)),
                'lang' : lang,
                }
            if defaults.DEBUG: print >>sys.stderr, command
            (error, output) = commands.getstatusoutput(command)
            if defaults.DEBUG: print >> sys.stderr, output
            
if __name__ == "__main__":
    import sys, os
    if len(sys.argv)>=1 and len(sys.argv)<=3:
        if os.access(defaults.modules_xml, os.R_OK):
            m = modules.XmlModules(defaults.modules_xml)
            if len(sys.argv)==3:
                module = sys.argv[1]
                branch = sys.argv[2]
                print "Updating stats for %s.%s..." % (module, branch)
                if module in m.keys():
                    LocStatistics(m[module], onlybranch=branch)
            elif len(sys.argv)==2:
                module = sys.argv[1]
                print "Updating stats for %s..." % (module)
                if module in m.keys():
                    LocStatistics(m[module])
            else:
                for modid in m:
                    print "Updating stats for %s..." % (modid)
                    LocStatistics(m[modid])
        else:
            print "Usage:\n\t%s [MODULE_ID [BRANCH]]\n" % (sys.argv[0])
    else:
        print "Usage:\n\t%s [MODULE_ID [BRANCH]]\n" % (sys.argv[0])

