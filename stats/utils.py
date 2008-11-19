# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2007 Danilo Segan <danilo@gnome.org>.
# Copyright (c) 2008 Claude Paroz <claude@2xlibre.net>.
#
# This file is part of Damned Lies.
#
# Damned Lies is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Damned Lies is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Damned Lies; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.utils.translation import ugettext as _, ugettext_noop
from stats.conf import settings
import sys, os, re, time, commands

def sortObjectList(lst, sort_meth):
    """ Sort an object list with sort_meth (which should return a translated string) """
    templist = [(getattr(obj_, sort_meth)().lower(), obj_) for obj_ in lst]
    templist.sort()
    return [obj_ for (key1, obj_) in templist]

def multiple_replace(dct, text):
    regex = re.compile("(%s)" % "|".join(map(re.escape, dct.keys())))
    return regex.sub(lambda mo: dct[mo.string[mo.start():mo.end()]], text)

def stripHTML(string):
    replacements = {"<ul>": "\n", "</ul>": "\n", "<li>": " * ", "\n</li>": "", "</li>": ""}
    return multiple_replace(replacements, string)

def check_potfiles(po_path):
    """Check if there were any problems regenerating a POT file (intltool-update -m).
       Return a list of errors """
    errors = []

    command = "cd \"%(dir)s\" && rm -f missing notexist && intltool-update -m" % { "dir" : po_path, }
    if settings.DEBUG: print >>sys.stderr, command
    (error, output) = commands.getstatusoutput(command)
    if settings.DEBUG: print >> sys.stderr, output

    if error:
        if settings.DEBUG: print >> sys.stderr, "Error running 'intltool-update -m' check."
        errors.append( ("error", ugettext_noop("Errors while running 'intltool-update -m' check.")) )

    missing = os.path.join(po_path, "missing")
    if os.access(missing, os.R_OK):
        f = open(missing, "r")
        errors.append( ("warn",
                        ugettext_noop("There are some missing files from POTFILES.in: %s")
                        % ("<ul><li>"
                        + "</li>\n<li>".join(f.readlines())
                        + "</li>\n</ul>")) )

    notexist = os.path.join(po_path, "notexist")
    if os.access(notexist, os.R_OK):
        f = open(notexist, "r")
        errors.append(("error",
                       ugettext_noop("Following files are referenced in either POTFILES.in or POTFILES.skip, yet they don't exist: %s")
                       % ("<ul><li>"
                       + "</li>\n<li>".join(f.readlines())
                       + "</li>\n</ul>")))
    return errors

def generate_doc_pot_file(vcs_path, potbase, moduleid, verbose):
    """ Return the pot file for a document-type domain, and the error if any """
    
    errors = []
    modulename = read_makefile_variable(vcs_path, "DOC_MODULE")
    if not modulename:
        return "", (("error", ugettext_noop("Module %s doesn't look like gnome-doc-utils module.") % moduleid),)
    if not os.access(os.path.join(vcs_path, "C", modulename + ".xml"), os.R_OK):
        if os.access(os.path.join(vcs_path, "C", moduleid + ".xml"), os.R_OK):
            errors.append(("warn", ugettext_noop("DOC_MODULE doesn't resolve to a real file, using '%s.xml'.") % (moduleid)))
            modulename = moduleid
        else:
            errors.append(("error", ugettext_noop("DOC_MODULE doesn't point to a real file, probably a macro.")))
            return "", errors
    
    files = os.path.join("C", modulename + ".xml")
    includes = read_makefile_variable(vcs_path, "DOC_INCLUDES")
    for f in includes.split(" "):
        if f.strip() != "":
            files += " %s" % (os.path.join("C", f.strip()))
    
    potfile = os.path.join(vcs_path, "C", potbase + ".pot")
    command = "cd \"%s\" && xml2po -o %s -e %s" % (vcs_path, potfile, files)
    if verbose: print >>sys.stderr, command
    (error, output) = commands.getstatusoutput(command)
    if error:
        errors.append(("error",
                       ugettext_noop("Error regenerating POT file for document %(file)s:\n<pre>%(cmd)s\n%(output)s</pre>")
                             % {'file': potbase,
                                'cmd': command,
                                'output': output})
                     )
    if verbose: print >> sys.stderr, output
    
    if error or not os.access(potfile, os.R_OK):
        return "", errors
    else:
        return potfile, errors

def read_makefile_variable(vcs_path, variable):
    makefileam = os.path.join(vcs_path, "Makefile.am")
    try:
        fin = open(makefileam, "r")
    except IOError:
        # probably file not found or unreadable
        return ""

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
                    incfile = os.path.join(os.path.dirname(makefileam), os.path.basename(match.group(1)))
                    if incfile.find("gnome-doc-utils.make")==-1:
                        if settings.DEBUG:
                            print >>sys.stderr, "Reading file %s..." % (incfile)
                        var = read_makefile_variable(incfile, variable)
                        if var != "":
                            return var

            fullline = ""
    return ""


def po_file_stats(pofile, msgfmt_checks = 1):

    errors = []

    try: os.stat(pofile)
    except OSError: errors.append(("error", ugettext_noop("PO file '%s' doesn't exist.") % pofile))

    if msgfmt_checks:
        command = "LC_ALL=C LANG=C LANGUAGE=C msgfmt -cv -o /dev/null %s" % pofile
    else:
        command = "LC_ALL=C LANG=C LANGUAGE=C msgfmt --statistics -o /dev/null %s" % pofile

    if settings.DEBUG: print >>sys.stderr, command
    (error, output) = commands.getstatusoutput(command)
    if settings.DEBUG: print >>sys.stderr, output

    if error:
        if msgfmt_checks:
            errors.append(("error", ugettext_noop("PO file '%s' doesn't pass msgfmt check: not updating.") % (os.path.basename(pofile))))
        else:
            errors.append(("error", ugettext_noop("Can't get statistics for POT file '%s'.") % (pofile)))

    if msgfmt_checks and os.access(pofile, os.X_OK):
        errors.append(("warn", ugettext_noop("This PO file has an executable bit set.")))

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
                   "diff -i -u %s - >/dev/null") % (pofile,
                                                    pofile)
        if settings.DEBUG: print >>sys.stderr, command
        (error, output) = commands.getstatusoutput(command)
        if settings.DEBUG: print >>sys.stderr, output
        if error:
            myfile = os.path.basename(pofile)
            errors.append(("warn",
                           ugettext_noop("PO file '%s' is not UTF-8 encoded.") % (myfile)))
    return {
        'translated' : translated,
        'fuzzy' : fuzzy,
        'untranslated' : untranslated,
        'errors' : errors,
        }


def check_lang_support(module_path, po_path, lang):
    """Checks if language is listed in one of po/LINGUAS, configure.ac or configure.in"""

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
                    if settings.DEBUG: print >>sys.stderr, "Language '%s' found in LINGUAS." % (lang)
                    in_config = 1
                    break
            lfile.close()
            if not in_config:
                errors.append(("warn", ugettext_noop("Entry for this language is not present in LINGUAS file.")))
            return errors

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
                test = re.search('ALL_LINGUAS\s*[=,]\s*"([^"]*)"', line)
                if test:
                    value = test.groups(1)[0]
                    if lang in value.split(" "):
                        if settings.DEBUG: print >>sys.stderr, "Language '%s' found in %s." % (lang, configure)
                        in_config = 1
                    break
            cfile.close()
            if not in_config:
                errors.append(("warn", ugettext_noop("Entry for this language is not present in ALL_LINGUAS in configure file.")))
            return errors

    errors.append(("warn", ugettext_noop("Don't know where to look if this language is actually used, ask the module maintainer.")))
    return errors

def copy_file(file1, file2):
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

def notify_list(out_domain, diff):
    """Send notification about string changes described in diff.

    Uses settings.NOTIFICATIONS_TO as "to" address,
    settings.WHOAREWE as "from" address, and sends
    using SMTP on localhost:25."""
    import smtplib
    from email.mime.text import MIMEText
    text = u"""This is an automatic notification from status generation scripts on:
%(ourweb)s.

There have been following string additions to module '%(module)s':

%(potdiff)s

Note that this doesn't directly indicate a string freeze break, but it
might be worth investigating.
""" % { 'module' : out_domain,
    'ourweb' : settings.WHEREAREWE,
    'potdiff' : "\n    ".join(diff).decode('utf-8') }

    msg = MIMEText(text.encode('utf-8'), 'plain', 'utf-8')
    msg['Subject'] = "String additions to '%s'" % (out_domain)
    msg['From'] = "GNOME Status Pages <%s>" % (settings.WHOAREWE)
    msg['To'] = settings.NOTIFICATIONS_TO

    s = smtplib.SMTP()
    s.connect()
    s.sendmail(settings.WHOAREWE, settings.NOTIFICATIONS_TO, msg.as_string())
    s.close()

class Profiler(object):
    def __init__(self):
        self.start = time.clock()
    
    def time_spent(self):
        return time.clock() - self.start 
