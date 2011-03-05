# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2007 Danilo Segan <danilo@gnome.org>.
# Copyright (c) 2008-2010 Claude Paroz <claude@2xlibre.net>.
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

import sys, os, re, time
import hashlib
from itertools import islice
from subprocess import Popen, PIPE
import errno

from django.utils.translation import ugettext_noop
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.files.base import File
from django.conf import settings

import potdiff

STATUS_OK = 0

NOT_CHANGED = 0
CHANGED_ONLY_FORMATTING = 1
CHANGED_WITH_ADDITIONS  = 2
CHANGED_NO_ADDITIONS    = 3

def sort_object_list(lst, sort_meth):
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

def run_shell_command(cmd, env=None, input_data=None, raise_on_error=False):
    if settings.DEBUG: print >>sys.stderr, cmd

    stdin = None
    if input_data:
        stdin = PIPE
    if env:
        os.environ.update(env)
        env = os.environ
    pipe = Popen(cmd, shell=True, env=env, stdin=stdin, stdout=PIPE, stderr=PIPE)
    if input_data:
        try:
            pipe.stdin.write(input_data)
        except IOError, e:
            if e.errno != errno.EPIPE:
                raise
    (output, errout) = pipe.communicate()
    status = pipe.returncode
    if settings.DEBUG: print >>sys.stderr, output + errout
    if raise_on_error and status != STATUS_OK:
        raise OSError(status, errout)

    return (status, output, errout)

def check_program_presence(prog_name):
    """ Test if prog_name is an available command on the system """
    status, output, err = run_shell_command("which %s" % prog_name)
    return status == 0

def check_potfiles(po_path):
    """Check if there were any problems regenerating a POT file (intltool-update -m).
       Return a list of errors """
    errors = []

    command = "cd \"%(dir)s\" && rm -f missing notexist && intltool-update -m" % { "dir" : po_path, }
    (status, output, errs) = run_shell_command(command)

    if status != STATUS_OK:
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
    xml2po_options = ""
    if os.access(os.path.join(vcs_path, "C", "index.page"), os.R_OK):
        # a Mallard document
        files = ["index.page"]
        includes = read_makefile_variable([vcs_path], "DOC_PAGES")
        xml2po_options = "-m mallard"

    else:
        modulename = read_makefile_variable([vcs_path], "DOC_MODULE")
        if not modulename:
            return "", (("error", ugettext_noop("Module %s doesn't look like gnome-doc-utils module.") % moduleid),)
        if not os.access(os.path.join(vcs_path, "C", modulename + ".xml"), os.R_OK):
            if os.access(os.path.join(vcs_path, "C", moduleid + ".xml"), os.R_OK):
                errors.append(("warn", ugettext_noop("DOC_MODULE doesn't resolve to a real file, using '%s.xml'.") % (moduleid)))
                modulename = moduleid
            else:
                # Last try: only one xml file in C/...
                xml_files = [f for f in os.listdir(os.path.join(vcs_path, "C")) if f.endswith(".xml")]
                if len(xml_files) == 1:
                    modulename = os.path.basename(xml_files[0])[:-4]
                else:
                    errors.append(("error", ugettext_noop("DOC_MODULE doesn't point to a real file, probably a macro.")))
                    return "", errors
        files = [modulename + ".xml"]
        includes = read_makefile_variable([vcs_path], "DOC_INCLUDES")

    if includes:
        files.extend(filter(lambda x:x not in ("", "$(NULL)"), includes.split()))
    files = " ".join([os.path.join("C", f) for f in files])
    potfile = os.path.join(vcs_path, "C", potbase + ".pot")
    command = "cd \"%s\" && xml2po %s -o %s -e %s" % (vcs_path, xml2po_options, potfile, files)
    (status, output, errs) = run_shell_command(command)

    if status != STATUS_OK:
        errors.append(("error",
                       ugettext_noop("Error regenerating POT file for document %(file)s:\n<pre>%(cmd)s\n%(output)s</pre>")
                             % {'file': potbase,
                                'cmd': command,
                                'output': errs})
                     )
        potfile = ""

    if not os.access(potfile, os.R_OK):
        return "", errors
    else:
        return potfile, errors

def read_makefile_variable(vcs_paths, variable):
    """ vcs_paths is a list of potential path where Makefile.am could be found """
    makefiles = [os.path.join(path, "Makefile.am") for path in vcs_paths]
    good_makefile = None
    for makefile in makefiles:
        if os.access(makefile, os.R_OK):
            good_makefile = makefile
            break
    if not good_makefile:
        return None # no file found

    return search_variable_in_file(good_makefile, variable)

def search_variable_in_file(file_path, variable):
    """ Search for a variable value in a file, and return content if found
        Return None if variable not found in file (or file does not exist)
    """
    try:
        file = open(file_path, "r")
    except IOError:
        return None

    non_terminated_content = ""
    found = None
    for line in file:
        line = line.strip()
        if non_terminated_content:
            line = non_terminated_content + " " + line
        # Test if line is non terminated (end with \ or even quote count)
        if (len(line)>2 and line[-1] == "\\") or line.count('"') % 2 == 1:
            if line[-1] == "\\":
                # Remove trailing backslash
                line = line[:-1]
            non_terminated_content = line
        else:
            non_terminated_content = ""
            # Search for variable
            match = re.search('%s\s*[=,]\s*"?([^"=]*)"?' % variable, line)
            if match:
                found = match.group(1)
                break
    file.close()
    return found

def pot_diff_status(pota, potb):
    (status, output, errs) = run_shell_command("diff %s %s|wc -l" % (pota, potb))
    # POT generation date always change and produce a 4 line diff
    if int(output) <= 4:
        return NOT_CHANGED, ""

    result_all, result_add_only = potdiff.diff(pota, potb)
    if not len(result_all) and not len(result_add_only):
        return CHANGED_ONLY_FORMATTING, ""
    elif len(result_add_only):
        return CHANGED_WITH_ADDITIONS, result_add_only
    else:
        return CHANGED_NO_ADDITIONS, result_all

def po_file_stats(pofile, msgfmt_checks=True, count_images=True):
    """ Compute pofile translation statistics, and proceed to some validity checks if msgfmt_checks is True """
    res = {
        'translated' : 0,
        'fuzzy' : 0,
        'untranslated' : 0,
        'num_figures' : 0,
        'errors' : [],
        }
    c_env = {"LC_ALL": "C", "LANG": "C", "LANGUAGE": "C"}

    if isinstance(pofile, basestring):
        # pofile is a filesystem path
        filename = os.path.basename(pofile)
        if not os.access(pofile, os.R_OK):
            res['errors'].append(("error", ugettext_noop("PO file '%s' does not exist or cannot be read.") % pofile))
            return res
        input_data = None
        input_file = pofile
    elif isinstance(pofile, File):
        filename = pofile.name
        input_data = pofile.read()
        input_file = "-"
    else:
        raise ValueError("pofile type not recognized")

    if msgfmt_checks:
        command = "msgfmt -cv -o /dev/null %s" % input_file
    else:
        command = "msgfmt --statistics -o /dev/null %s" % input_file

    (status, output, errs) = run_shell_command(command, env=c_env, input_data=input_data)

    if status != STATUS_OK:
        if msgfmt_checks:
            res['errors'].append(("error", ugettext_noop("PO file '%s' doesn't pass msgfmt check: not updating.") % (filename)))
        else:
            res['errors'].append(("error", ugettext_noop("Can't get statistics for POT file '%s'.") % (pofile)))

    if msgfmt_checks and input_file != "-" and os.access(pofile, os.X_OK):
        res['errors'].append(("warn", ugettext_noop("This PO file has an executable bit set.")))

    # msgfmt output stats on stderr
    r_tr = re.search(r"([0-9]+) translated", errs)
    r_un = re.search(r"([0-9]+) untranslated", errs)
    r_fz = re.search(r"([0-9]+) fuzzy", errs)

    if r_tr:
        res['translated'] = int(r_tr.group(1))
    if r_un:
        res['untranslated'] = int(r_un.group(1))
    if r_fz:
        res['fuzzy'] = int(r_fz.group(1))

    if msgfmt_checks:
        # Check if PO file is in UTF-8
        if input_file == "-":
            try:
                input_data.decode('UTF-8')
                status = STATUS_OK
            except:
                status = STATUS_OK+1
        else:
            command = ("msgconv -t UTF-8 %s | diff -i -I '^#~' -u %s - >/dev/null") % (pofile,
                                                                              pofile)
            (status, output, errs) = run_shell_command(command, env=c_env)
        if status != STATUS_OK:
            res['errors'].append(("warn",
                              ugettext_noop("PO file '%s' is not UTF-8 encoded.") % (filename)))
    # Count number of figures in PO(T) file
    if count_images:
        command = "grep '^msgid \"@@image:' \"%s\" | wc -l" % pofile
        (status, output, errs) = run_shell_command(command)
        res['num_figures'] = int(output)

    return res

def read_linguas_file(full_path):
    """ Read a LINGUAS file (each language code on a line by itself) """
    langs = []
    lfile = open(full_path, "r")
    [langs.extend(line.split()) for line in lfile if line[:1]!='#']
    lfile.close()
    return {'langs':langs,
            'error': ugettext_noop("Entry for this language is not present in LINGUAS file.") }

def get_ui_linguas(module_path, po_path):
    """Get language list in one of po/LINGUAS, configure.ac or configure.in"""

    LINGUAShere = os.path.join(po_path, "LINGUAS")
    LINGUASpo = os.path.join(module_path, "po", "LINGUAS") # if we're in eg. po-locations/
    configureac = os.path.join(module_path, "configure.ac")
    configurein = os.path.join(module_path, "configure.in")

    # is "lang" listed in either of po/LINGUAS, ./configure.ac(ALL_LINGUAS) or ./configure.in(ALL_LINGUAS)
    for LINGUAS in [LINGUAShere, LINGUASpo]:
        if os.access(LINGUAS, os.R_OK):
            return read_linguas_file(LINGUAS)
    for configure in [configureac, configurein]:
        found = search_variable_in_file(configure, 'ALL_LINGUAS')
        if found is not None:
            return {'langs': found.split(),
                    'error': ugettext_noop("Entry for this language is not present in ALL_LINGUAS in configure file.") }
    return {'langs':None,
            'error': ugettext_noop("Don't know where to look for the LINGUAS variable, ask the module maintainer.") }

def get_doc_linguas(module_path, po_path):
    """Get language list in one Makefile.am (either path) """
    linguas = read_makefile_variable([po_path, module_path], "DOC_LINGUAS")
    if linguas is None:
        return {'langs':None,
                'error': ugettext_noop("Don't know where to look for the DOC_LINGUAS variable, ask the module maintainer.") }
    return {'langs': linguas.split(),
            'error': ugettext_noop("DOC_LINGUAS list doesn't include this language.") }

def get_fig_stats(pofile):
    """ Extract image strings from pofile and return a list of figures dict:
        [{'path':, 'video':, 'hash':, 'fuzzy':, 'translated':}, ...] """
    # Extract image strings: beforeline/msgid/msgstr/grep auto output a fourth line
    command = "msgcat --no-wrap %(pofile)s| grep -A 1 -B 1 '^msgid \"@@image:'" % locals()
    (status, output, errs) = run_shell_command(command)
    if status != STATUS_OK:
        # FIXME: something should be logged here
        return []
    lines = output.split('\n')
    while lines[0][0] != "#":
        lines = lines[1:] # skip warning messages at the top of the output
    re_path = re.compile('^msgid \"@@image: \'([^\']*)\'')
    re_hash = re.compile('.*md5=(.*)\"')
    figures = []

    for i, line in islice(enumerate(lines), 0, None, 4):
        fig = {'path': '', 'hash': '', 'video': False}
        fig['fuzzy'] = (line=='#, fuzzy' or line[:8]=='#| msgid')
        path_match = re_path.match(lines[i+1])
        if path_match and len(path_match.groups()):
            fig['path'] = path_match.group(1)
            fig['video'] = fig['path'].endswith(".ogv")
        hash_match = re_hash.match(lines[i+1])
        if hash_match and len(hash_match.groups()):
            fig['hash'] = hash_match.group(1)
        fig['translated'] = len(lines[i+2])>9 and not fig['fuzzy']
        figures.append(fig)
    return figures

def add_custom_header(po_path, header, value):
    """ Add a custom po file header """
    grep_cmd = """grep "%s" %s""" % (header, po_path)
    status = 1
    last_headers = ["Content-Transfer-Encoding", "Plural-Forms"]
    while status != 0 and last_headers != []:
        (status, output, errs) = run_shell_command(grep_cmd)
        if status != 0:
            # Try to add header
            cmd = '''sed -i '/^\"%s/ a\\"%s: %s\\\\n"' %s''' % (last_headers.pop(), header, value, po_path)
            (stat, out, err) = run_shell_command(cmd)
    if status == 0 and not "%s: %s" % (header, value) in output:
        # Set header value
        cmd = '''sed -i '/^\"%s/ c\\"%s: %s\\\\n"' %s''' % (header, header, value, po_path)
        (stat, out, err) = run_shell_command(cmd)

def is_po_reduced(file_path):
    status, output, errs = run_shell_command("""grep "X-DamnedLies-Scope: partial" %s""" % file_path)
    return (status == 0)

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

def compute_md5(full_path):
    m = hashlib.md5()
    block_size=2**13
    f = open(full_path)
    while True:
        data = f.read(block_size)
        if not data:
            break
        m.update(data)
    f.close()
    return m.hexdigest()


def notify_list(out_domain, diff):
    """Send notification about string changes described in diff."""
    current_site = Site.objects.get_current()
    text = u"""This is an automatic notification from status generation scripts on:
http://%(ourweb)s.

There have been following string additions to module '%(module)s':

%(potdiff)s

Note that this doesn't directly indicate a string freeze break, but it
might be worth investigating.
""" % { 'module' : out_domain,
    'ourweb' : current_site.domain,
    'potdiff' : "\n    ".join(diff).decode('utf-8') }

    send_mail(subject="String additions to '%s'" % (out_domain),
              message=text,
              from_email="GNOME Status Pages <%s>" % (settings.DEFAULT_FROM_EMAIL),
              recipient_list=settings.NOTIFICATIONS_TO)

def url_join(base, *args):
    """ Create an url in joining base with arguments. A lot nicer than urlparse.urljoin! """
    url = base
    for arg in args:
        if url[-1] != "/":
            url += "/"
        url += arg
    return url

class Profiler(object):
    def __init__(self):
        self.start = time.clock()

    def time_spent(self):
        return time.clock() - self.start
