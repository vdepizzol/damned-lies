# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Claude Paroz <claude@2xlibre.net>.
# Copyright (c) 2008 Stephane Raimbault <stephane.raimbault@gmail.com>.
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

import os, sys, re, commands
import threading
from datetime import datetime
from time import tzname
from itertools import islice
from django.db import models, connection
from django.utils.translation import ungettext, ugettext as _, ugettext_noop
from stats.conf import settings
from stats import utils
import potdiff

from people.models import Person
from languages.models import Language

VCS_TYPE_CHOICES = (
    ('cvs', 'CVS'), 
    ('svn', 'Subversion'), 
    ('git', 'Git'),
    ('hg', 'Mercurial'),
    ('bzr', 'Bazaar')
)

BRANCH_HEAD_NAMES = (
    'HEAD',
    'trunk',
    'master'
)

class Module(models.Model):
    name = models.CharField(max_length=50)
    homepage = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    bugs_base = models.CharField(max_length=50)
    bugs_product = models.CharField(max_length=50)
    bugs_component = models.CharField(max_length=50)
    vcs_type = models.CharField(max_length=5, choices=VCS_TYPE_CHOICES)
    vcs_root = models.URLField(verify_exists=False)
    vcs_web = models.URLField()
    
    maintainers = models.ManyToManyField(Person, db_table='module_maintainer',
        related_name='maintains_modules', blank=True)

    class Meta:
        db_table = 'module'
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ('stats.views.module', [self.name])

    def get_description(self):
        if self.description:
            return _(self.description)
        else:
            return self.name
    
    def get_bugs_i18n_url(self):
        if self.bugs_base.find("bugzilla") != -1 or self.bugs_base.find("freedesktop") != -1:
            return "%sbuglist.cgi?product=%s&amp;component=%s&amp;keywords_type=anywords&amp;keywords=I18N+L10N&amp;bug_status=UNCONFIRMED&amp;bug_status=NEW&amp;bug_status=ASSIGNED&amp;bug_status=REOPENED&amp;bug_status=NEEDINFO" % (self.bugs_base, self.bugs_product, self.bugs_component)
        else:
            return None

    def get_bugs_enter_url(self):
        if self.bugs_base.find("bugzilla") != -1 or self.bugs_base.find("freedesktop") != -1:
            return "%senter_bug.cgi?product=%s&amp;component=%s" % (self.bugs_base, self.bugs_product, self.bugs_component)
        else:
            return self.bugs_base 
    
    def get_branches(self):
        branches = list(self.branch_set.all())
        branches.sort()
        return branches
    
    def get_head_branch(self):
        """ Returns the HEAD (trunk, master, ...) branch of the module """
        branch = self.branch_set.filter(name__in = BRANCH_HEAD_NAMES)
        if branch:
            # First one (if many something is wrong :-/)
            return branch[0]
        else:
            return None
    
    def can_edit_branches(self, user):
        """ Returns True for superusers, users with adequate permissions or maintainers of the module """ 
        if user.is_superuser or \
           user.has_perms(['stats.delete_branch', 'stats.add_branch', 'stats.change_branch']) or \
           user.username in [ p.username for p in self.maintainers.all() ]:
            return True
        return False

class BranchCharField(models.CharField):
    def pre_save(self, model_instance, add):
        """ Check if branch is valid before saving the instance """
        if not model_instance.checkout():
            raise Exception, "Branch not valid: error while checking out the branch."
        return getattr(model_instance, self.attname)

class Branch(models.Model):
    """ Branch of a module """
    name = BranchCharField(max_length=50)
    #description = models.TextField(null=True)
    vcs_subpath = models.CharField(max_length=50, null=True, blank=True)
    module = models.ForeignKey(Module)
    # 'releases' is the backward relation name from Release model

    class Meta:
        db_table = 'branch'
        verbose_name_plural = 'branches'
        ordering = ('name',)
        unique_together = ("name", "module")

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.module)

    def save(self):
        super(Branch, self).save()
        # The update command is launched asynchronously in a separate thread
        upd_thread = threading.Thread(target=self.update_stats, kwargs={'force':True})
        upd_thread.start()

    def __cmp__(self, other):
        if self.name in BRANCH_HEAD_NAMES:
            return -1
        elif other.name in BRANCH_HEAD_NAMES:
            return 1
        else:
            return -cmp(self.name, other.name)

    def is_head(self):
        return self.name in BRANCH_HEAD_NAMES

    def has_string_frozen(self):
        """ Returns true if the branch is contained in at least one string frozen release """
        return self.releases.filter(string_frozen=True).count() and True or False
           
    def get_vcs_url(self):
        if self.module.vcs_type in ('hg', 'git'):
            return "%s/%s" % (self.module.vcs_root, self.module_name)
        elif self.vcs_subpath:
            return "%s/%s/%s" % (self.module.vcs_root, self.module.name, self.vcs_subpath)
        elif self.is_head():
            return "%s/%s/trunk" % (self.module.vcs_root, self.module.name)
        else:
            return "%s/%s/branches/%s" % (self.module.vcs_root, self.module.name, self.name)

    def get_vcs_web_url(self):
        if self.is_head():
            return "%s/trunk" % (self.module.vcs_web)
        else:
            return "%s/branches/%s" % (self.module.vcs_web, self.name)

    def co_path(self):
        """ Returns the path of the local checkout for the branch """
        return os.path.join(settings.SCRATCHDIR, self.module.vcs_type, self.module.name + "." + self.name)
    
    def output_dir(self, dom_type):
        """ Directory where generated pot and po files are written on local system """
        subdir = {'ui': '', 'doc': 'docs'}[dom_type]
        dirname = os.path.join(settings.POTDIR, self.module.name + "." + self.name, subdir)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return dirname
    
    def get_stats(self, typ):
        """ Get statistics list of type typ ('ui' or 'doc'), in a dict of lists, key is domain.name (POT in 1st position)"""
        stats = {}
        for stat in self.statistics_set.all():
            if stat.domain.dtype == typ:
                if stats.has_key(stat.domain.name):
                    if stat.language:
                        stats[stat.domain.name].append(stat)
                    else:
                        stats[stat.domain.name].insert(0, stat) # This is the POT file
                else:
                    stats[stat.domain.name] = [stat,]
        # Sort
        for key, doms in stats.items():
            doms.sort(self.compare_stats)
        return stats
    
    def compare_stats(self, a, b):
        """ Sort stats, pot first, then translated (desc), then language name """
        if not a.language:
            return -1
        elif not b.language:
            return 1
        else:
            res = -cmp(a.translated, b.translated)
            if not res:
                res = cmp(a.get_lang(), b.get_lang())
        return res  
    
    def get_doc_stats(self):
        return self.get_stats('doc')

    def get_ui_stats(self):
        return self.get_stats('ui')
    
    def update_stats(self, force):
        """ Update statistics for all po files from the branch """
        self.checkout()
        domains = Domain.objects.filter(module=self.module).all()
        string_frozen = self.has_string_frozen()
        for dom in domains:
            # 1. Initial settings
            # *******************
            domain_path = os.path.join(self.co_path(), dom.directory)
            if not os.access(domain_path, os.X_OK):
                # TODO: should check if existing stats, and delete (archive) them in this case
                continue
            errors = []
            
            # 2. Pre-check, if available (intltool-update -m)
            # **************************
            if dom.dtype == 'ui' and not dom.pot_method:
                # Run intltool-update -m to check for some errors
                errors.extend(utils.check_potfiles(domain_path))
            
            # 3. Generate a fresh pot file
            # ****************************
            if dom.dtype == 'ui':
                potfile, errs = dom.generate_pot_file(domain_path)
            elif dom.dtype == 'doc': # only gnome-doc-utils toolchain supported so far for docs
                potfile, errs = utils.generate_doc_pot_file(domain_path, dom.potbase(), self.module.name, settings.DEBUG)
                doclinguas = utils.read_makefile_variable(domain_path, "DOC_LINGUAS").split()
            else:
                print >> sys.stderr, "Unknown domain type '%s', ignoring domain '%s'" % (dom.dtype, dom.name)
                continue 
            errors.extend(errs)
            
            # 4. Compare with old pot files, various checks
            # *****************************
            previous_pot = os.path.join(self.output_dir(dom.dtype), dom.potbase() + "." + self.name + ".pot")
            if not potfile:
                if settings.DEBUG: print >> sys.stderr, "Can't generate POT file for %s/%s." % (self.module.name, dom.directory)
                if os.access(previous_pot, os.R_OK):
                    # Use old POT file
                    potfile = previous_pot
                    errors.append(("error", ugettext_noop("Can't generate POT file, using old one.")))
                else:
                    # Not sure if we should do something here
                    continue

            pot_has_changed = True

            # If old pot already exists and we are in string freeze
            if os.access(previous_pot, os.R_OK):
                if string_frozen and dom.dtype == 'ui':
                    diff = potdiff.diff(previous_pot, potfile, 1)
                    if len(diff):
                        utils.notify_list("%s.%s" % (self.module.name, self.name), diff)

                # If old pot already exists, lets see if it has changed at all
                diff = potdiff.diff(previous_pot, potfile)
                if not len(diff):
                    pot_has_changed = False
            
            # 5. Generate pot stats and update DB
            # ***********************************
            pot_stats = utils.po_file_stats(potfile, 0)
            errors.extend(pot_stats['errors'])
            if potfile != previous_pot and not utils.copy_file(potfile, previous_pot):
                errors.append(('error', ugettext_noop("Can't copy new POT file to public location.")))

            try:
                stat = Statistics.objects.get(language=None, branch=self, domain=dom)
                stat.untranslated = int(pot_stats['untranslated'])
                stat.date = datetime.now()
                Information.objects.filter(statistics=stat).delete()
            except Statistics.DoesNotExist:
                stat = Statistics(language = None, branch = self, domain = dom, translated = 0,
                                  fuzzy = 0, untranslated = int(pot_stats['untranslated']))
            stat.save()
            for err in errors:
                stat.information_set.add(Information(type=err[0], description=err[1]))
            
            # 6. Update language po files and update DB
            # *****************************************
            command = "msgmerge -o %(outpo)s %(pofile)s %(potfile)s"
            for lang, pofile in self.get_lang_files(dom, domain_path):
                outpo = os.path.join(self.output_dir(dom.dtype), dom.potbase() + "." + self.name + "." + lang + ".po")

                if not force and not pot_has_changed and os.access(outpo, os.R_OK) and os.stat(pofile)[8] < os.stat(outpo)[8]:
                    continue

                realcmd = command % {
                    'outpo' : outpo,
                    'pofile' : pofile,
                    'potfile' : potfile,
                    }
                if settings.DEBUG: print >>sys.stderr, realcmd
                (error, output) = commands.getstatusoutput(realcmd)
                if settings.DEBUG: print >> sys.stderr, output

                langstats = utils.po_file_stats(outpo, 1)
                if dom.dtype == "ui":
                    langstats['errors'].extend(utils.check_lang_support(self.co_path(), domain_path, lang))
                elif dom.dtype == "doc":
                    if lang not in doclinguas:
                        langstats['errors'].append(("warn", ugettext_noop("DOC_LINGUAS list doesn't include this language.")))

                if settings.DEBUG: print >>sys.stderr, lang + ":\n" + str(langstats)
                # Save in DB
                try:
                    stat = Statistics.objects.get(language__locale=lang, branch=self, domain=dom)
                    stat.translated = int(langstats['translated'])
                    stat.fuzzy = int(langstats['fuzzy'])
                    stat.untranslated = int(langstats['untranslated'])
                    stat.date = datetime.now()
                    Information.objects.filter(statistics=stat).delete()
                except Statistics.DoesNotExist:
                    try:
                        language = Language.objects.get(locale=lang)
                    except Language.DoesNotExist:
                        language = Language(name=lang, locale=lang)
                        language.save()
                    stat = Statistics(language = language, branch = self, domain = dom, translated = int(langstats['translated']),
                                      fuzzy = int(langstats['fuzzy']), untranslated = int(langstats['untranslated']))
                stat.save()
                for err in langstats['errors']:
                    stat.information_set.add(Information(type=err[0], description=err[1])) 
    
    def get_lang_files(self, domain, dom_path):
        """ Returns a list of language files on filesystem, as tuple (lang, lang_file) -> lang_file with complete path """
        flist = []
        if domain.dtype == "ui":
            for f in os.listdir(dom_path):
                # FIXME: temporary fix for ooo-build module (see #551328)
                if f[-3:] != ".po" or f[:4] == "ooo-":
                    continue
                lang = f[:-3]
                pofile = os.path.join(dom_path, f)
                flist.append((lang, pofile))
        if domain.dtype == "doc":
            for d in os.listdir(dom_path):
                pofile = os.path.join(dom_path, d, d + ".po")
                if os.path.isfile(pofile):
                    flist.append((d, pofile))
        return flist
    
    def checkout(self):
        """ Do a checkout or an update of the VCS files """
        module_name = self.module.name
        vcs_type = self.module.vcs_type
        localroot = os.path.join(settings.SCRATCHDIR, vcs_type)
        moduledir = self.module.name + "." + self.name
        modulepath = os.path.join(localroot, moduledir)
        scmroot = self.module.vcs_root

        try: os.makedirs(localroot)
        except: pass
        
        commandList = []
        if os.access(modulepath, os.X_OK | os.W_OK):
            # Path exists, update repos
            if vcs_type == "cvs":
                commandList.append("cd \"%(localdir)s\" && cvs -z4 up -Pd" % {
                    "localdir" : modulepath,
                    })
            elif vcs_type == "svn":
                commandList.append("cd \"%(localdir)s\" && svn up --non-interactive" % {
                    "localdir" : modulepath,
                    })
            elif vcs_type == "hg":
                commandList.append("cd \"%(localdir)s\" && hg revert --all" % {
                    "localdir" : modulepath,
                    })
            elif vcs_type == "git":
                commandList.append("cd \"%(localdir)s\" && git checkout %(branch)s && git reset --hard && git clean -df" % {
                    "localdir" : modulepath,
                    "branch" : self.name,
                    })
            elif vcs_type == "bzr":
                commandList.append("cd \"%(localdir)s\" && bzr up" % {
                    "localdir" : modulepath,
                    })
        else:
            # Checkout
            vcs_path = self.get_vcs_url()
            if vcs_type == "cvs":
                commandList.append("cd \"%(localroot)s\" && cvs -d%(cvsroot)s -z4 co -d%(dir)s -r%(branch)s %(module)s" % {
                "localroot" : localroot,
                "cvsroot" : scmroot,
                "dir" : moduledir,
                "branch" : self.name,
                "module" : module_name,
                })
            elif vcs_type == "svn":
                commandList.append("cd \"%(localroot)s\" && svn co --non-interactive %(svnpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "svnpath" : vcs_path,
                    "dir" : moduledir,
                    })
            elif vcs_type == "hg":
                commandList.append("cd \"%(localroot)s\" && hg clone %(hgpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "hgpath" : vcs_path,
                    "dir" : moduledir,
                    })
                commandList.append("cd \"%(localdir)s\" && hg update %(branch)s" % {
                    "localdir" : modulepath,
                    "branch" : self.name,
                    })
            elif vcs_type == "git":
                commandList.append("cd \"%(localroot)s\" && git clone %(gitpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "gitpath" : vcs_path,
                    "dir" : moduledir,
                    })
                commandList.append("cd \"%(localdir)s\" && git checkout %(branch)s" % {
                    "localdir" : modulepath,
                    "branch" : self.name,
                    })
            elif vcs_type == "bzr":
                commandList.append("cd \"%(localroot)s\" && bzr co --lightweight %(bzrpath)s \"%(dir)s\"" % {
                    "localroot" : localroot,
                    "bzrpath" : vcs_path,
                    "dir" : moduledir,
                    })
        
        # Run command(s)
        errorsOccured = 0
        if settings.DEBUG:
            print >>sys.stdout, "Checking '%s.%s' out to '%s'..." % (module_name, self.name, modulepath)
        for command in commandList:
            if settings.DEBUG:
                print >>sys.stdout, command
            (error, output) = commands.getstatusoutput(command)
            if settings.DEBUG:
                print >> sys.stderr, output
            if error:
                errorsOccured = 1
                if settings.DEBUG:
                    print >> sys.stderr, error
        if errorsOccured:
            print >> sys.stderr, "Problem checking out module %s.%s" % (module_name, self.name)
            return 0
        else:
            return 1


DOMAIN_TYPE_CHOICES = (
    ('ui', 'User Interface'),
    ('doc', 'Documentation')
)

class Domain(models.Model):
    module = models.ForeignKey(Module)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    dtype = models.CharField(max_length=5, choices=DOMAIN_TYPE_CHOICES, default='ui')
    directory = models.CharField(max_length=50)
    # The pot_method is a command who chould produce a potfile in the po directory of
    # the domain, named <potbase()>.pot (e.g. /po/gnucash.pot). If blank, method is 
    # intltool for UI and gnome-doc-utils for DOC
    pot_method = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'domain'

    def __unicode__(self):
        return self.get_dtype_display()

    def potbase(self):
        if self.name[:2] == 'po':
            # e.g. replace po by gimp (for ui), or po-plugins by gimp-plugins
            return self.module.name + self.name[2:]
        elif self.name == 'help':
            return "%s-help" % self.module.name
        else:
            return self.name
    
    def get_description(self):
        return self.description or self.potbase()
    
    def generate_pot_file(self, vcs_path):
        """ Return the pot file generated, and the error if any """
        
        pot_command = self.pot_method
        podir = vcs_path
        if not self.pot_method: # default is intltool
            pot_command = r"""XGETTEXT_ARGS="\"--msgid-bugs-address=%(bugs_enterurl)s\"" intltool-update -g '%(domain)s' -p""" % {
                               'bugs_enterurl': self.module.get_bugs_enter_url(),
                               'domain': self.potbase()
                               }
        elif self.module.name == 'damned-lies':
            # special case for d-l, pot file should be generated from running instance dir
            podir = "."
            vcs_path = "./po"
        command = "cd \"%(dir)s\" && %(pot_command)s" % {
            "dir" : podir,
            "pot_command" : pot_command,
            }
        if settings.DEBUG: print >>sys.stderr, command
        (error, output) = commands.getstatusoutput(command)
        if settings.DEBUG: print >> sys.stderr, output

        potfile = os.path.join(vcs_path, self.potbase() + ".pot")

        if error or not os.access(potfile, os.R_OK):
            return "", (("error", ugettext_noop("Error regenerating POT file for %(file)s:\n<pre>%(cmd)s\n%(output)s</pre>")
                                 % {'file': self.potbase(),
                                    'cmd': pot_command,
                                    'output': output.decode('utf-8')}),
                       )
        else:
            return potfile, ()
    
RELEASE_STATUS_CHOICES = (
    ('official', 'Official'),
    ('unofficial', 'Unofficial'),
    ('xternal', 'External')
)
class Release(models.Model):
    name = models.SlugField(max_length=20)
    description = models.CharField(max_length=50)
    string_frozen = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=RELEASE_STATUS_CHOICES)
    branches = models.ManyToManyField(Branch, through='Category', related_name='releases')

    class Meta:
        db_table = 'release'
        ordering = ('status', '-name')

    def __unicode__(self):
        return self.description
    
    def total_strings(self):
        """ Returns the total number of strings in the release as a tuple (doc_total, ui_total) """
        # Uses the special statistics record where language_id is NULL to compute the sum.
        query = """
            SELECT domain.dtype, 
                   SUM(stat.untranslated)
            FROM statistics AS stat
            LEFT JOIN domain 
                   ON domain.id = stat.domain_id
            LEFT JOIN branch AS br
                   ON br.id = stat.branch_id
            LEFT JOIN category AS cat
                   ON cat.branch_id = br.id
            LEFT JOIN "release" AS rel
                   ON rel.id = cat.release_id 
            WHERE rel.id = %s
              AND stat.language_id IS NULL
            GROUP BY domain.dtype"""
        cursor = connection.cursor()
        if settings.DATABASE_ENGINE == 'mysql':
            cursor.execute("SET sql_mode='ANSI_QUOTES'")
        cursor.execute(query, (self.id,))

        total_doc, total_ui = 0, 0
        for row in cursor.fetchall():
            if row[0] == 'ui':
                total_ui = row[1]
            elif row[0] == 'doc':
                total_doc = row[1]
        return (total_doc, total_ui)
    
    def total_for_lang(self, lang):
        """ Returns total translated/fuzzy/untranslated strings for a specific
            language """
        
        total_doc, total_ui = self.total_strings()
        query = """
            SELECT domain.dtype,
                   SUM(stat.translated), 
                   SUM(stat.fuzzy) 
            FROM statistics AS stat
            LEFT JOIN domain 
                   ON stat.domain_id = domain.id
            LEFT JOIN branch 
                   ON stat.branch_id = branch.id
            LEFT JOIN category 
                   ON category.branch_id = branch.id 
            WHERE language_id = %s 
              AND category.release_id = %s
            GROUP BY domain.dtype"""
        cursor = connection.cursor()
        cursor.execute(query, (lang.id, self.id))
        stats = {'id': self.id, 'name': self.name, 'description': _(self.description),
                 'uitrans': 0, 'uifuzzy': 0, 'uitotal': total_ui,
                 'doctrans': 0, 'docfuzzy': 0, 'doctotal': total_doc,
                 'uitransperc': 0, 'uifuzzyperc': 0, 'uiuntransperc': 0,
                 'doctransperc': 0, 'docfuzzyperc': 0, 'docuntransperc': 0}
        for res in cursor.fetchall():
            if res[0] == 'ui':
                stats['uitrans'] = res[1]
                stats['uifuzzy'] = res[2]
            if res[0] == 'doc':
                stats['doctrans'] = res[1]
                stats['docfuzzy'] = res[2]
        stats['uiuntrans'] = total_ui - (stats['uitrans'] + stats['uifuzzy'])
        if total_ui > 0:
            stats['uitransperc'] = int(100*stats['uitrans']/total_ui)
            stats['uifuzzyperc'] = int(100*stats['uifuzzy']/total_ui)
            stats['uiuntransperc'] = int(100*stats['uiuntrans']/total_ui)
        stats['docuntrans'] = total_doc - (stats['doctrans'] + stats['docfuzzy'])
        if total_doc > 0:
            stats['doctransperc'] = int(100*stats['doctrans']/total_doc)
            stats['docfuzzyperc'] = int(100*stats['docfuzzy']/total_doc)
            stats['docuntransperc'] = int(100*stats['docuntrans']/total_doc)
        return stats
    
    def get_global_stats(self):
        """ Get statistics for all languages in a release, grouped by language
            Returns a sorted list: (language, doc_trans, doc_fuzzy,
            doc_untrans, ui_trans, ui_fuzzy, ui_untrans) """

        query = """
            SELECT MIN(lang.name), 
                   MIN(lang.locale), 
                   domain.dtype, 
                   SUM(stat.translated) AS trans, 
                   SUM(stat.fuzzy)
            FROM statistics AS stat
            LEFT JOIN domain 
                   ON domain.id = stat.domain_id
            LEFT JOIN language AS lang 
                   ON stat.language_id = lang.id
            LEFT JOIN branch AS br
                   ON br.id = stat.branch_id
            LEFT JOIN category
                   ON category.branch_id = br.id
            WHERE category.release_id = %s AND stat.language_id IS NOT NULL
            GROUP BY domain.dtype, stat.language_id
            ORDER BY domain.dtype, trans DESC"""
        cursor = connection.cursor()
        cursor.execute(query, (self.id,))
        stats = {}
        total_docstrings, total_uistrings = self.total_strings()
        for row in cursor.fetchall():
            if not stats.has_key(row[1]):
                # Initialize stats dict
                stats[row[1]] = {
                    'lang_name': row[0], 'lang_locale': Language.slug_locale(row[1]),
                    'doc_trans': 0, 'doc_fuzzy': 0, 'doc_untrans': total_docstrings,
                    'doc_percent': 0, 'doc_percentfuzzy': 0, 'doc_percentuntrans': 100,
                    'ui_trans': 0, 'ui_fuzzy': 0, 'ui_untrans': total_uistrings,
                    'ui_percent': 0, 'ui_percentfuzzy': 0, 'ui_percentuntrans': 100}
            if row[2] == 'doc':
                stats[row[1]]['doc_trans'] = row[3]
                stats[row[1]]['doc_fuzzy'] = row[4]
                stats[row[1]]['doc_untrans'] = total_docstrings - (row[3] + row[4])
                if total_docstrings > 0:
                    stats[row[1]]['doc_percent'] = int(100*row[3]/total_docstrings)
                    stats[row[1]]['doc_percentfuzzy'] = int(100*row[4]/total_docstrings)
                    stats[row[1]]['doc_percentuntrans'] = int(100*stats[row[1]]['doc_untrans']/total_docstrings)
            if row[2] == 'ui':
                stats[row[1]]['ui_trans'] = row[3]
                stats[row[1]]['ui_fuzzy'] = row[4]
                stats[row[1]]['ui_untrans'] = total_uistrings - (row[3] + row[4])
                if total_uistrings > 0:
                    stats[row[1]]['ui_percent'] = int(100*row[3]/total_uistrings)
                    stats[row[1]]['ui_percentfuzzy'] = int(100*row[4]/total_uistrings)
                    stats[row[1]]['ui_percentuntrans'] = int(100*stats[row[1]]['ui_untrans']/total_uistrings)
        cursor.close()

        results = stats.values()
        results.sort(self.compare_stats)
        return results 
    
    def compare_stats(self, a, b):
        res = cmp(b['ui_trans'], a['ui_trans'])
        if not res:
            res = cmp(b['doc_trans'], a['doc_trans'])
            if not res:
                res = cmp(b['lang_name'], a['lang_name'])
        return res  
    
    def get_lang_stats(self, lang):
        """ Get statistics for a specific language, producing the stats data structure
            Used for displaying the language-release template """
        
        # Sorted by module to allow grouping ('fake' stats)
        pot_stats = Statistics.objects.filter(language=None, branch__releases=self).order_by('domain__module__id', 'domain__dtype')
        stats = {'doc':{'dtype':'doc', 'totaltrans':0, 'totalfuzzy':0, 'totaluntrans':0, 'categs':{}, 'all_errors':[]}, 
                 'ui':{'dtype':'ui', 'totaltrans':0, 'totalfuzzy':0, 'totaluntrans':0, 'categs':{}, 'all_errors':[]} 
                }
        for stat in pot_stats:
            dtype = stat.domain.dtype
            categdescr = stat.branch.category_set.get(release=self).name
            domname = _(stat.domain.description)
            modname = stat.domain.module.name
            if not stats[dtype]['categs'].has_key(categdescr):
                stats[dtype]['categs'][categdescr] = {'cattrans':0, 'catfuzzy':0, 
                                                      'catuntrans':0, 'modules':{}}
            stats[dtype]['totaluntrans'] += stat.untranslated
            stats[dtype]['categs'][categdescr]['catuntrans'] += stat.untranslated
            if not stats[dtype]['categs'][categdescr]['modules'].has_key(modname):
                # first element is a placeholder for a fake stat
                stats[dtype]['categs'][categdescr]['modules'][modname] = {' fake':None, domname:stat}
                previous_domname = domname
            else:
                if len(stats[dtype]['categs'][categdescr]['modules'][modname]) < 3:
                    # Create a fake statistics object for module summary
                    stats[dtype]['categs'][categdescr]['modules'][modname][' fake'] = FakeStatistics(stat.domain.module, dtype)
                    stats[dtype]['categs'][categdescr]['modules'][modname][' fake'].untrans(stats[dtype]['categs'][categdescr]['modules'][modname][previous_domname])
                stats[dtype]['categs'][categdescr]['modules'][modname][domname] = stat
                stats[dtype]['categs'][categdescr]['modules'][modname][' fake'].untrans(stat)
            #stats[dtype]['categs'][categdescr]['modules']["%s-%s" % (stat.branch.id, stat.domain.id)] = stat
        
        # Second pass for translated stats
        tr_stats = Statistics.objects.filter(language=lang, branch__releases=self).order_by('domain__module__id')
        for stat in tr_stats:
            dtype = stat.domain.dtype
            categdescr = stat.branch.category_set.get(release=self).name
            domname = _(stat.domain.description)
            modname = stat.domain.module.name
            stats[dtype]['totaltrans'] += stat.translated
            stats[dtype]['totalfuzzy'] += stat.fuzzy
            stats[dtype]['totaluntrans'] -= (stat.translated + stat.fuzzy)
            stats[dtype]['categs'][categdescr]['cattrans'] += stat.translated
            stats[dtype]['categs'][categdescr]['catfuzzy'] += stat.fuzzy
            stats[dtype]['categs'][categdescr]['catuntrans'] -= (stat.translated + stat.fuzzy)
            if stats[dtype]['categs'][categdescr]['modules'][modname][' fake']:
                stats[dtype]['categs'][categdescr]['modules'][modname][' fake'].trans(stat)
            # Replace POT stat by translated stat
            stats[dtype]['categs'][categdescr]['modules'][modname][domname] = stat
            stats[dtype]['all_errors'].extend(stat.information_set.all())
        
        # Compute percentages and sorting
        for dtype in ['ui', 'doc']:
            stats[dtype]['total'] = stats[dtype]['totaltrans'] + stats[dtype]['totalfuzzy'] + stats[dtype]['totaluntrans']
            if stats[dtype]['total'] > 0:
                stats[dtype]['totaltransperc'] = int(100*stats[dtype]['totaltrans']/stats[dtype]['total'])
                stats[dtype]['totalfuzzyperc'] = int(100*stats[dtype]['totalfuzzy']/stats[dtype]['total'])
                stats[dtype]['totaluntransperc'] = int(100*stats[dtype]['totaluntrans']/stats[dtype]['total'])
            else:
                stats[dtype]['totaltransperc'] = 0
                stats[dtype]['totalfuzzyperc'] = 0
                stats[dtype]['totaluntransperc'] = 0
            for key, categ in stats[dtype]['categs'].items():
                categ['catname'] = Category.get_cat_name(key)
                categ['cattotal'] = categ['cattrans'] + categ['catfuzzy'] + categ['catuntrans']
                categ['cattransperc'] = int(100*categ['cattrans']/categ['cattotal'])
                # Sort modules
                mods = [[name,mod] for name, mod in categ['modules'].items()]
                mods.sort()
                categ['modules'] = mods
                # Sort domains
                for mod in categ['modules']:
                    doms = [(name,dom) for name, dom in mod[1].items()]
                    doms.sort()
                    mod[1] = doms
            # Sort errors
            stats[dtype]['all_errors'].sort()
        return stats

    def get_lang_files(self, lang, dtype):
        """ Return a list of all po files of a lang for this release, preceded by the more recent modification date
            It uses the POT file if there is no po for a module """
        pot_stats = Statistics.objects.filter(language=None, branch__releases=self, domain__dtype=dtype)
        po_stats = Statistics.objects.filter(language=lang, branch__releases=self, domain__dtype=dtype)
        lang_files = []
        last_modif_date = datetime(1970, 01, 01)
        # Create list of files
        for stat in pot_stats:
            if stat.date > last_modif_date:
                last_modif_date = stat.date
            try:
                lang_stat = po_stats.get(branch = stat.branch, domain = stat.domain)
            except Statistics.DoesNotExist:
                lang_stat = stat
            file_path = lang_stat.po_path()
            if os.access(file_path, os.R_OK):
                lang_files.append(file_path)
        return last_modif_date, lang_files


CATEGORY_CHOICES = (
    ('default', 'Default'),
    ('admin-tools', ugettext_noop('Administration Tools')),
    ('dev-tools', ugettext_noop('Development Tools')),
    ('desktop', ugettext_noop('GNOME Desktop')),
    ('dev-platform', ugettext_noop('GNOME Developer Platform')),
    ('proposed', ugettext_noop('New Module Proposals')),
)
class Category(models.Model):
    release = models.ForeignKey(Release)
    branch = models.ForeignKey(Branch)
    name = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='default')

    class Meta:
        db_table = 'category'
        verbose_name_plural = 'categories'
        unique_together = ("release", "branch")

    def __unicode__(self):
        return "%s (%s, %s)" % (self.get_name_display(), self.release, self.branch)
    
    @classmethod
    def get_cat_name(cls, key):
        for entry in CATEGORY_CHOICES:
            if key == entry[0]:
                return _(entry[1])
        return key

class Statistics(models.Model):
    branch = models.ForeignKey(Branch)
    domain = models.ForeignKey(Domain)
    language = models.ForeignKey(Language, null=True)
    
    date = models.DateTimeField(auto_now_add=True)
    translated = models.IntegerField(default=0)
    fuzzy = models.IntegerField(default=0)
    untranslated = models.IntegerField(default=0)

    class Meta:
        db_table = 'statistics'
        verbose_name = "statistics"
        verbose_name_plural = verbose_name

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.figures = None
        self.modname = None
        self.partial_po = False # True if part of a multiple po module
    
    def __unicode__(self):
        """ String representation of the object """
        return "%s (%s-%s) %s (%s)" % (self.branch.module.name, self.domain.dtype, self.domain.name,
                                       self.branch.name, self.get_lang())

    def is_fake(self):
        return False
        
    def tr_percentage(self):
        if self.pot_size() == 0:
            return 0
        else:
            return int(100*self.translated/self.pot_size())
    
    def fu_percentage(self):
        if self.pot_size() == 0:
            return 0
        else:
            return int(100*self.fuzzy/self.pot_size())
    
    def un_percentage(self):
        if self.pot_size() == 0:
            return 0
        else:
            return int(100*self.untranslated/self.pot_size())

    def get_lang(self):
        if self.language:
            return _("%(lang_name)s (%(lang_locale)s)") % { 
                'lang_name': self.language.name,
                'lang_locale': self.language.locale
            }
        else:
            return "pot file"
    
    def module_name(self):
        if not self.modname:
            self.modname = self.branch.module.name
        return self.modname
    
    def module_description(self):
        return self.branch.module.description
        
    def get_translationstat(self):
        return "%d%%&nbsp;(%d/%d/%d)" % (self.tr_percentage(), self.translated, self.fuzzy, self.untranslated)
    
    def filename(self):
        if self.language:
            return "%s.%s.%s.po" % (self.domain.potbase(), self.branch.name, self.language.locale)
        else:
            return "%s.%s.pot" % (self.domain.potbase(), self.branch.name)
            
    def pot_size(self):
        return int(self.translated) + int(self.fuzzy) + int(self.untranslated)
    
    def pot_text(self):
        """ Return stat table header: 'POT file (n messages) - updated on ??-??-???? tz' """
        msg_text = ungettext(u"%(count)s message", "%(count)s messages", self.pot_size()) % {'count': self.pot_size()}
        upd_text = _(u"updated on %(date)s") % {'date': self.date.strftime("%Y-%m-%d %H:%M:%S ")+tzname[0]}
        if self.fig_count():
            fig_text = ungettext(u"%(count)s figure", "%(count)s figures", self.fig_count()) % {'count': self.fig_count()}
            text = _(u"POT file (%(messages)s, %(figures)s) — %(updated)s") % \
                              {'messages': msg_text, 'figures': fig_text, 'updated': upd_text}
        else:
            text = _(u"POT file (%(messages)s) — %(updated)s") % \
                              {'messages': msg_text, 'updated': upd_text}
        return text
    
    def get_figures(self):
        if self.figures is None and self.domain.dtype == 'doc':
            # Extract image strings: beforeline/msgid/msgstr/grep auto output a fourth line 
            command = "msgcat --no-wrap %(pofile)s| grep -A 1 -B 1 '^msgid \"@@image:'" % { 'pofile': self.po_path() }
            (error, output) = commands.getstatusoutput(command)
            if error:
                # FIXME: something should be logged here
                return []
            lines = output.split('\n')
            while lines[0][0] != "#":
                lines = lines[1:] # skip warning messages at the top of the output
            re_path = re.compile('^msgid \"@@image: \'([^\']*)\'')
            self.figures = []
            
            for i, line in islice(enumerate(lines), 0, None, 4):
                fig = {}
                fig['fuzzy'] = line=='#, fuzzy'
                path_match = re_path.match(lines[i+1])
                if path_match and len(path_match.groups()):
                    fig['path'] = path_match.group(1)
                else:
                    fig['path'] = '' # This should not happen
                fig['translated'] = len(lines[i+2])>9 and not fig['fuzzy']
                fig['translated_file'] = False
                if self.language:
                    # Check if a translated figure really exists or if the English one is used
                    if os.path.exists(os.path.join(self.branch.co_path(), self.domain.directory, self.language.locale, fig['path'])):
                        fig['translated_file'] = True
                self.figures.append(fig)
        return self.figures
    
    def fig_count(self):
        """ If stat of a document type, get the number of figures in the document """
        return len(self.get_figures() or [])
    
    def fig_stats(self):
        stats = {'fuzzy':0, 'translated':0, 'total':0, 'prc':0}
        for fig in self.get_figures():
            stats['total'] += 1
            if fig['fuzzy']: stats['fuzzy'] += 1
            else:
                if fig['translated']: stats['translated'] += 1
        stats['untranslated'] = stats['total'] - (stats['translated'] + stats['fuzzy'])
        if stats['total'] > 0:
            stats['prc'] = 100*stats['translated']/stats['total']
        return stats
            
    def vcs_path(self):
        """ Return the VCS path of file on remote vcs """
        return os.path.join(self.branch.get_vcs_url(), self.domain.directory)
        
    def vcs_web_path(self):
        """ Return the Web interface path of file on remote vcs """
        return os.path.join(self.branch.get_vcs_web_url(), self.domain.directory)
        
    def po_path(self):
        """ Return path of po file on local filesystem """
        subdir = ""
        if self.domain.dtype == "doc":
            subdir = "docs"
        return os.path.join(settings.POTDIR, self.module_name()+'.'+self.branch.name, subdir, self.filename())
        
    def po_url(self):
        """ Return URL of po file, e.g. for downloading the file """
        if self.domain.dtype == "doc":
            subdir = "docs/"
        else:
            subdir = ""
        return "/POT/%s.%s/%s%s" % (self.module_name(), self.branch.name, subdir, self.filename())
        
    def most_important_message(self):
        """ Return a message of type 1.'error', or 2.'warn, or 3.'warn """
        error = None
        for e in self.information_set.all():
            if not error or e.type == 'error' or (e.type == 'warn' and error.type == 'info'):
                error = e
        return error
        
class FakeStatistics(object):
    """ This is a fake statistics class where a summary value is needed for a multi-domain module
        This is used in get_lang_stats for the language-release-stats template """
    def __init__(self, module, dtype):
        self.module = module
        self.dtype = dtype
        self.translated = 0
        self.fuzzy = 0
        self.untranslated = 0
        self.partial_po = False
    
    def untrans(self, stat):
        """ Called for POT file, so only untranslated is concerned """
        self.untranslated += stat.untranslated
        stat.partial_po = True
    
    def trans(self, stat):
        self.translated += stat.translated
        self.fuzzy += stat.fuzzy
        self.untranslated -= (stat.translated + stat.fuzzy)
        stat.partial_po = True
    
    def is_fake(self):
        return True
        
    def pot_size(self):
        return int(self.translated) + int(self.fuzzy) + int(self.untranslated)
    def tr_percentage(self):
        if self.pot_size() == 0:
            return 0
        else:
            return int(100*self.translated/self.pot_size())
    def fu_percentage(self):
        if self.pot_size() == 0:
            return 0
        else:
            return int(100*self.fuzzy/self.pot_size())
    def un_percentage(self):
        if self.pot_size() == 0:
            return 0
        else:
            return int(100*self.untranslated/self.pot_size())
    def module_name(self):
        return self.module.name
    def module_description(self):
        return self.module.description
       

class ArchivedStatistics(models.Model):
    module = models.TextField()
    type = models.CharField(max_length=3, choices=DOMAIN_TYPE_CHOICES)
    domain = models.TextField()
    branch = models.TextField()
    language = models.CharField(max_length=15)
    date = models.DateTimeField()
    translated = models.IntegerField(default=0)
    fuzzy = models.IntegerField(default=0)
    untranslated = models.IntegerField(default=0)

    class Meta:
        db_table = 'archived_statistics'

INFORMATION_TYPE_CHOICES = (
    ('info', 'Information'),
    ('warn','Warning'),
    ('error','Error')
)
class Information(models.Model):
    statistics = models.ForeignKey('Statistics')
    # Priority of a stats message
    type = models.CharField(max_length=5, choices=INFORMATION_TYPE_CHOICES)
    description = models.TextField()

    class Meta:
        db_table = 'information'

    def __cmp__(self, other):
        return cmp(self.statistics.module_name(), other.statistics.module_name())

    def get_icon(self):
        return "/media/img/%s.png" % self.type
    
    def get_description(self):
        text = self.description
        matches = re.findall('###([^#]*)###',text) 
        if matches:
            text = re.sub('###([^#]*)###', '%s', text)

        text = _(text)
        
        #FIXME: if multiple substitutions, works only if order of %s is unchanged in translated string
        for match in matches:
        	  text = text.replace('%s',match,1)
        return text

class ArchivedInformation(models.Model):
    statistics = models.ForeignKey('ArchivedStatistics')
    # Priority of a stats message
    type = models.CharField(max_length=5, choices=INFORMATION_TYPE_CHOICES)
    description = models.TextField()

    class Meta:
        db_table = 'archived_information'

