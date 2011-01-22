# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2010 Claude Paroz <claude@2xlibre.net>.
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

from __future__ import with_statement
import os, sys, re, hashlib
import threading
from time import sleep
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ungettext, ugettext as _, ugettext_noop
from django.utils import dateformat
from django.utils.datastructures import SortedDict
from django.db import models, connection

from common.fields import DictionaryField
from stats import utils, signals
from stats.doap import update_doap_infos
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
    homepage    = models.URLField(null=True, blank=True,
                      help_text="Automatically updated if the module contains a doap file.")
    description = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    bugs_base = models.CharField(max_length=50, null=True, blank=True)
    bugs_product = models.CharField(max_length=50, null=True, blank=True)
    bugs_component = models.CharField(max_length=50, null=True, blank=True)
    vcs_type = models.CharField(max_length=5, choices=VCS_TYPE_CHOICES)
    # URLField is too restrictive for vcs_root
    vcs_root = models.CharField(max_length=200)
    vcs_web = models.URLField()

    maintainers = models.ManyToManyField(Person, db_table='module_maintainer',
        related_name='maintains_modules', blank=True,
        help_text="Automatically updated if the module contains a doap file.")

    class Meta:
        db_table = 'module'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('stats.views.module', [self.name])

    def save(self, force_insert=False, force_update=False):
        super(Module, self).save(force_insert, force_update)
        #FIXME: delete and recreate branch if vcs_root changed?

    def get_description(self):
        return self.description and _(self.description) or self.name

    def get_comment(self):
        return self.comment and _(self.comment) or ""

    def has_standard_vcs(self):
        """ This function checks if the module is hosted in the standard VCS of the project """
        return re.search(settings.VCS_HOME_REGEX, self.vcs_root) is not None

    def get_bugs_i18n_url(self):
        if self.bugs_base.find("bugzilla") != -1 or self.bugs_base.find("freedesktop") != -1:
            return utils.url_join(self.bugs_base,
                                    "buglist.cgi?product=%s&keywords_type=anywords&keywords=I18N+L10N&bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=NEEDINFO" % (self.bugs_product,))
        else:
            return None

    def get_bugs_enter_url(self):
        if self.bugs_base.find("bugzilla") != -1 or self.bugs_base.find("freedesktop") != -1:
            if self.bugs_component:
                return utils.url_join(self.bugs_base, "enter_bug.cgi?product=%s&component=%s" % (self.bugs_product, self.bugs_component))
            else:
                return utils.url_join(self.bugs_base, "enter_bug.cgi?product=%s" % (self.bugs_product,))
        else:
            return self.bugs_base

    def get_branches(self, reverse=False):
        """ Return module branches, in ascending order by default (descending order if reverse == True) """
        branches = list(self.branch_set.all())
        branches.sort(reverse=reverse)
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

class ModuleLock(object):
    """ Weird things happen when multiple updates run in parallel for the same module
        We use filesystem directories creation/deletion to act as global lock mecanism
    """
    def __init__(self, mod):
        assert isinstance(mod, Module)
        self.module = mod

    def __enter__(self):
        self.dirpath = os.path.join("/tmp", "updating-%s" % (self.module.name,))
        while True:
            try:
                os.mkdir(self.dirpath)
                break;
            except OSError:
                sleep(30)

    def __exit__(self, *exc_info):
        os.rmdir(self.dirpath)

class Branch(models.Model):
    """ Branch of a module """
    name        = models.CharField(max_length=50)
    #description = models.TextField(null=True)
    vcs_subpath = models.CharField(max_length=50, null=True, blank=True)
    module      = models.ForeignKey(Module)
    weight      = models.IntegerField(default=0, help_text="Smaller weight is displayed first")
    file_hashes = DictionaryField(default='', blank=True, editable=False)
    # 'releases' is the backward relation name from Release model

    # May be set to False by test suite
    checkout_on_creation = True

    class Meta:
        db_table = 'branch'
        verbose_name_plural = 'branches'
        ordering = ('name',)
        unique_together = ('name', 'module')

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.checkout_lock = threading.Lock()
        self._ui_stats = None
        self._doc_stats = None

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.module)

    def clean(self):
        if self.checkout_on_creation:
            try:
                self.checkout()
            except:
                raise ValidationError("Branch not valid: error while checking out the branch (%s)." % sys.exc_info()[1])

    def save(self, force_insert=False, force_update=False, update_statistics=True):
        super(Branch, self).save(force_insert, force_update)
        if update_statistics:
            # The update command is launched asynchronously in a separate thread
            upd_thread = threading.Thread(target=self.update_stats, kwargs={'force':True})
            upd_thread.start()

    def delete(self):
        import shutil # os.rmdir cannot delete non-empty dirs
        # Remove the repo checkout
        if self.module.vcs_type in ('cvs', 'svn'):
            if os.access(self.co_path(), os.W_OK):
                shutil.rmtree(self.co_path())
        elif self.module.vcs_type == 'git':
            if self.is_head():
                if os.access(self.co_path(), os.W_OK):
                    shutil.rmtree(self.co_path())
            else:
                cmd = "cd \"%(localdir)s\" && git checkout master && git branch -D %(branch)s" % {
                    'localdir': self.co_path(),
                    'branch': self.name,
                }
                utils.run_shell_command(cmd)
        #To be implemented for hg/bzr

        # Remove the pot/po generated files
        if os.access(self.output_dir('ui'), os.W_OK):
            shutil.rmtree(self.output_dir('ui'))
        super(Branch, self).delete()

    def __cmp__(self, other):
        if self.name in BRANCH_HEAD_NAMES:
            return -1
        elif other.name in BRANCH_HEAD_NAMES:
            return 1
        return cmp(self.weight, other.weight) or -cmp(self.name, other.name)

    @property
    def img_url_prefix(self):
        return self.module.vcs_type == 'git' and "plain" or ""

    @property
    def img_url_suffix(self):
        return self.module.vcs_type == 'git' and "?h=%s" % self.name or ""

    def is_head(self):
        return self.name in BRANCH_HEAD_NAMES

    def warnings(self):
        if self.releases.count() < 1:
            return _(u"This branch is not linked from any release")
        return ""

    def file_changed(self, rel_path):
        """ This method determine if some file has changed based on its hash
            Always returns true if this is the first time the path is checked
        """
        full_path = os.path.join(self.co_path(), rel_path)
        if not os.access(full_path, os.R_OK):
            return False # Raise exception?
        new_hash = utils.compute_md5(full_path)
        if self.file_hashes.get(rel_path, None) == new_hash:
            return False
        else:
            self.file_hashes[rel_path] = new_hash
            self.save(update_statistics=False)
            return True

    def has_string_frozen(self):
        """ Returns true if the branch is contained in at least one string frozen release """
        return self.releases.filter(string_frozen=True).count() and True or False

    def get_vcs_url(self):
        if self.module.vcs_type in ('hg', 'git'):
            return self.module.vcs_root
        elif self.vcs_subpath:
            return utils.url_join(self.module.vcs_root, self.module.name, self.vcs_subpath)
        elif self.is_head():
            return utils.url_join(self.module.vcs_root, self.module.name, "trunk")
        else:
            return utils.url_join(self.module.vcs_root, self.module.name, "branches", self.name)

    def is_vcs_readonly(self):
        return self.module.vcs_root.find('ssh://') == -1

    def get_vcs_web_url(self):
        if self.module.vcs_type in ('hg', 'git'):
            return self.module.vcs_web
        elif self.vcs_subpath:
            return utils.url_join(self.module.vcs_web, self.vcs_subpath)
        elif self.is_head():
            return utils.url_join(self.module.vcs_web, "trunk")
        else:
            return utils.url_join(self.module.vcs_web, "branches", self.name)

    def co_path(self):
        """ Returns the path of the local checkout for the branch """
        if self.module.vcs_type in ('hg', 'git'):
            branch_dir = self.module.name
        else:
            branch_dir = self.module.name + "." + self.name
        return os.path.join(settings.SCRATCHDIR, self.module.vcs_type, branch_dir)

    def output_dir(self, dom_type):
        """ Directory where generated pot and po files are written on local system """
        subdir = {'ui': '', 'doc': 'docs'}[dom_type]
        dirname = os.path.join(settings.POTDIR, self.module.name + "." + self.name, subdir)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return dirname

    def get_stats(self, typ, mandatory_langs=[]):
        """ Get statistics list of type typ ('ui' or 'doc'), in a dict of lists, key is domain.name (POT in 1st position)
            stats = {'po':      [potstat, polang1, polang2, ...],
                     'po-tips': [potstat, polang1, polang2, ...]}
            mandatory_langs is a list of language objects whose stats should be added even if no translation exists.
        """
        stats = SortedDict(); stats_langs = {}
        pot_stats = Statistics.objects.select_related("language", "domain", "branch"
                        ).filter(branch=self, language__isnull=True, domain__dtype=typ
                        ).order_by('domain__name')
        for stat in pot_stats.all():
            stats[stat.domain.name] = [stat,]
            stats_langs[stat.domain.name] = []
        tr_stats = Statistics.objects.select_related("language", "domain", "branch").filter(branch=self, language__isnull=False, domain__dtype=typ)
        for stat in tr_stats.all():
            stats[stat.domain.name].append(stat)
            stats_langs[stat.domain.name].append(stat.language)
        # Check if all mandatory languages are present
        for lang in mandatory_langs:
            for domain in stats.keys():
                if lang not in stats_langs[domain]:
                    fake_stat = FakeStatistics(self.module, self, typ, lang)
                    fake_stat.untranslated = stats[domain][0].untranslated
                    stats[domain].append(fake_stat)
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

    def get_doc_stats(self, mandatory_langs=[]):
        if not self._doc_stats:
            self._doc_stats = self.get_stats('doc', mandatory_langs)
        return self._doc_stats

    def get_ui_stats(self, mandatory_langs=[]):
        if not self._ui_stats:
            self._ui_stats = self.get_stats('ui', mandatory_langs)
        return self._ui_stats

    def update_stats(self, force, checkout=True):
        """ Update statistics for all po files from the branch """
        with ModuleLock(self.module):
            if checkout:
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
                    potfile, errs = dom.generate_pot_file(self)
                elif dom.dtype == 'doc':
                    if dom.pot_method:
                        potfile, errs = dom.generate_pot_file(self)
                    else:
                        # Standard gnome-doc-utils pot generation
                        potfile, errs = utils.generate_doc_pot_file(domain_path, dom.potbase(), self.module.name, settings.DEBUG)
                else:
                    print >> sys.stderr, "Unknown domain type '%s', ignoring domain '%s'" % (dom.dtype, dom.name)
                    continue
                errors.extend(errs)
                linguas = dom.get_linguas(self.co_path())
                if linguas['langs'] is None and linguas['error']:
                    errors.append(("warn", linguas['error']))

                # Prepare statistics object
                try:
                    stat = Statistics.objects.get(language=None, branch=self, domain=dom)
                    Information.objects.filter(statistics=stat).delete() # Reset errors
                except Statistics.DoesNotExist:
                    stat = Statistics(language=None, branch=self, domain=dom)
                    stat.save()

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
                        errors.append(("error", ugettext_noop("Can't generate POT file, statistics aborted.")))
                        stat.set_errors(errors)
                        continue

                changed_status = utils.CHANGED_WITH_ADDITIONS

                if os.access(previous_pot, os.R_OK):
                    # Compare old and new POT
                    changed_status, diff = utils.pot_diff_status(previous_pot, potfile)
                    if string_frozen and dom.dtype == 'ui' and changed_status == utils.CHANGED_WITH_ADDITIONS:
                        utils.notify_list("%s.%s" % (self.module.name, self.name), diff)

                    if changed_status != utils.NOT_CHANGED:
                        signals.pot_has_changed.send(sender=self, potfile=potfile, branch=self, domain=dom)

                # 5. Generate pot stats and update DB
                # ***********************************
                pot_stats = utils.po_file_stats(potfile, False)
                errors.extend(pot_stats['errors'])
                if potfile != previous_pot and not utils.copy_file(potfile, previous_pot):
                    errors.append(('error', ugettext_noop("Can't copy new POT file to public location.")))

                stat.set_translation_stats(previous_pot, untranslated=int(pot_stats['untranslated']), num_figures=int(pot_stats['num_figures']))
                stat.set_errors(errors)

                # 6. Update language po files and update DB
                # *****************************************
                command = "msgmerge --previous -o %(outpo)s %(pofile)s %(potfile)s"
                stats_with_ext_errors = Statistics.objects.filter(branch=self, domain=dom, information__type__endswith='-ext')
                langs_with_ext_errors = [stat.language.locale for stat in stats_with_ext_errors]
                for lang, pofile in dom.get_lang_files(self.co_path()):
                    outpo = os.path.join(self.output_dir(dom.dtype), dom.potbase() + "." + self.name + "." + lang + ".po")

                    if not force and changed_status in (utils.NOT_CHANGED, utils.CHANGED_ONLY_FORMATTING) and os.access(outpo, os.R_OK) \
                       and os.stat(pofile)[8] < os.stat(outpo)[8] and not lang in langs_with_ext_errors :
                        continue

                    realcmd = command % {
                        'outpo' : outpo,
                        'pofile' : pofile,
                        'potfile' : potfile,
                        }
                    utils.run_shell_command(realcmd)

                    langstats = utils.po_file_stats(outpo, True)
                    if linguas['langs'] is not None and lang not in linguas['langs']:
                        langstats['errors'].append(("warn-ext", linguas['error']))
                    if dom.dtype == "doc":
                        fig_stats = utils.get_fig_stats(outpo)
                        for fig in fig_stats:
                            trans_path = os.path.join(domain_path, lang, fig['path'])
                            if os.access(trans_path, os.R_OK):
                                fig_file = open(trans_path, 'rb').read()
                                trans_hash = hashlib.md5(fig_file).hexdigest()
                                if fig['hash'] == trans_hash:
                                    langstats['errors'].append(("warn-ext", "Figures should not be copied when identical to original (%s)." % trans_path))

                    if settings.DEBUG: print >>sys.stderr, lang + ":\n" + str(langstats)
                    # Save in DB
                    try:
                        stat = Statistics.objects.get(language__locale=lang, branch=self, domain=dom)
                        Information.objects.filter(statistics=stat).delete()
                    except Statistics.DoesNotExist:
                        try:
                            language = Language.objects.get(locale=lang)
                        except Language.DoesNotExist:
                            if self.is_head():
                                language = Language(name=lang, locale=lang)
                                language.save()
                            else:
                                # Do not create language (and therefore ignore stats) for an 'old' branch
                                continue
                        stat = Statistics(language = language, branch = self, domain = dom)
                        stat.save()
                    stat.set_translation_stats(outpo,
                                               translated = int(langstats['translated']),
                                               fuzzy = int(langstats['fuzzy']),
                                               untranslated = int(langstats['untranslated']),
                                               num_figures = int(langstats['num_figures']))
                    for err in langstats['errors']:
                        stat.information_set.add(Information(type=err[0], description=err[1]))
            # Check if doap file changed
            if self.is_head() and self.file_changed("%s.doap" % self.module.name):
                update_doap_infos(self.module)

    def _exists(self):
        """ Determine if branch (self) already exists (i.e. already checked out) on local FS """
        if self.module.vcs_type == 'git':
            command = "cd %s && git branch | grep %s" % (self.co_path(), self.name)
            status, output, errs = utils.run_shell_command(command)
            return output != ""
        elif self.module.vcs_type == 'hg':
            return self.id != None and os.access(self.co_path(), os.X_OK | os.W_OK)
        else:
            return os.access(self.co_path(), os.X_OK | os.W_OK)

    def checkout(self):
        """ Do a checkout or an update of the VCS files """
        module_name = self.module.name
        vcs_type = self.module.vcs_type
        localroot = os.path.join(settings.SCRATCHDIR, vcs_type)
        modulepath = self.co_path()
        scmroot = self.module.vcs_root

        try: os.makedirs(localroot)
        except: pass

        commandList = []
        if self._exists():
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
                # tester "cd \"%(localdir)s\" && git checkout %(branch)s && git clean -dfq && git pull origin/%(branch)s"
                commandList.append("cd \"%(localdir)s\" && git checkout %(branch)s && git fetch && git reset --hard origin/%(branch)s && git clean -dfq" % {
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
            if vcs_type in ('hg', 'git'):
                moduledir = self.module.name
            else:
                moduledir = self.module.name + "." + self.name

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
                # We are assuming here that master is the first branch created
                if self.name == "master":
                    commandList.append("cd \"%(localroot)s\" && git clone %(gitpath)s \"%(dir)s\"" % {
                        "localroot" : localroot,
                        "gitpath" : vcs_path,
                        "dir" : moduledir,
                        })
                    commandList.append("cd \"%(localdir)s\" && git remote update && git checkout %(branch)s" % {
                        "localdir" : modulepath,
                        "branch" : self.name,
                        })
                else:
                    commandList.append("cd \"%(localdir)s\" && git pull && git checkout --track -b %(branch)s  origin/%(branch)s" % {
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
        if settings.DEBUG:
            print >>sys.stdout, "Checking '%s.%s' out to '%s'..." % (module_name, self.name, modulepath)
        # Do not allow 2 checkouts to run in parallel on the same branch
        self.checkout_lock.acquire()
        try:
            for command in commandList:
                utils.run_shell_command(command, raise_on_error=True)
        finally:
            self.checkout_lock.release()
        return 1

    def commit_po(self, po_file, domain, language, user):
        """ Commit the file 'po_file' in the branch VCS repository """
        if self.is_vcs_readonly():
            raise Exception, "This branch is in read-only mode. Unable to commit"
        vcs_type = self.module.vcs_type
        if vcs_type not in ("git",):
            raise Exception, "Commit is not implemented for '%s'" % vcs_type

        locale = language.locale
        commit_dir = os.path.join(self.co_path(), domain.directory)
        dest_filename = "%s.po" % locale
        dest_path = os.path.join(commit_dir, dest_filename)
        already_exist = os.access(dest_path, os.F_OK)

        # Copy file in repo
        utils.copy_file(po_file, dest_path)

        if vcs_type == "git":
            var_dict = {
                'dest':    commit_dir,
                'branch':  self.name,
                'po_file': dest_filename,
                'lg_file': "LINGUAS",
                'name':    user.name,
                'email':   user.email,
                'msg':     "Updated %s translation" % language.name,
            }
            with ModuleLock(self.module):
                utils.run_shell_command("cd \"%(dest)s\" && git checkout %(branch)s" % var_dict, raise_on_error=True)
                # git add file.po
                utils.run_shell_command("cd \"%(dest)s\" && git add %(po_file)s" % var_dict, raise_on_error=True)
                if not already_exist:
                    # Add locale to LINGUAS
                    linguas_file = os.path.join(commit_dir, "LINGUAS")
                    if os.access(linguas_file, os.F_OK):
                        fin = open(linguas_file, 'r')
                        fout = open(linguas_file+"~", 'w')
                        lang_written = False
                        for line in fin:
                            if not lang_written and line[0] != "#" and line[:5] > locale[:5]:
                                fout.write(locale + "\n")
                                lang_written = True
                            fout.write(line)
                        fout.close()
                        fin.close()
                        os.rename(linguas_file+"~", linguas_file)
                        utils.run_shell_command("cd \"%(dest)s\" && git add %(lg_file)s" % var_dict, raise_on_error=True)
                    var_dict['msg'] = "Added %s translation" % language.name
                # git commit -m "Updated %s translation."
                utils.run_shell_command("cd \"%(dest)s\" && git commit -m \"%(msg)s\" --author \"%(name)s <%(email)s>\"" % var_dict,
                    raise_on_error=True)
                # git push
                utils.run_shell_command("cd \"%(dest)s\" && git push" % var_dict, raise_on_error=True)
        # Finish by updating stats
        self.update_stats(force=False)


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
    # The pot_method is a command who should produce a potfile in the po directory of
    # the domain, named <potbase()>.pot (e.g. /po/gnucash.pot).
    pot_method = models.CharField(max_length=100, null=True, blank=True,
        help_text="Leave blank for standard method (intltool for UI and gnome-doc-utils for DOC)")
    linguas_location = models.CharField(max_length=50, null=True, blank=True,
        help_text="""Use 'no' for no LINGUAS check, or path/to/file#variable for a non-standard location.
            Leave blank for standard location (ALL_LINGUAS in LINGUAS/configure.ac/.in for UI and DOC_LINGUAS in Makefile.am for DOC)""")

    class Meta:
        db_table = 'domain'
        ordering = ('-dtype', 'name')

    def __unicode__(self):
        return "%s (%s/%s)" % (self.name, self.module.name, self.get_dtype_display())

    def potbase(self):
        if self.name[:2] == 'po':
            # e.g. replace po by gimp (for ui), or po-plugins by gimp-plugins
            return self.module.name + self.name[2:]
        elif self.name == 'help':
            return "%s-help" % self.module.name
        else:
            return self.name

    def get_description(self):
        if self.description:
            return _(self.description)
        else:
            return self.potbase()

    def get_type(self, branch):
        """ Returns the type of the domain (ui, docbook, mallard) """
        if self.dtype == "ui":
            return "ui"
        else:
            if os.access(os.path.join(branch.co_path(), self.directory, "C", "index.page"), os.R_OK):
                return "mallard"
            else:
                return "docbook"

    def get_lang_files(self, base_path):
        """ Returns a list of language files on filesystem, as tuple (lang, lang_file) -> lang_file with complete path """
        flist = []
        dom_path = os.path.join(base_path, self.directory)
        for item in os.listdir(dom_path):
            # FIXME: temporary fix for ooo-build module (see #551328)
            if item[-3:] == ".po" and item[:4] != "ooo-":
                lang = item[:-3]
                pofile = os.path.join(dom_path, item)
                flist.append((lang, pofile))
            elif os.path.isdir(os.path.join(dom_path, item)):
                for base_name in [item, self.name.replace("~","/")]:
                    pofile = os.path.join(dom_path, item, base_name + ".po")
                    if os.access(pofile, os.F_OK):
                        flist.append((item, pofile))
                        break
        return flist

    def generate_pot_file(self, current_branch):
        """ Return the pot file generated, and the error if any """

        vcs_path = os.path.join(current_branch.co_path(), self.directory)
        pot_command = self.pot_method
        podir = vcs_path
        env = None
        if not self.pot_method: # default is intltool
            env = {"XGETTEXT_ARGS": "\"--msgid-bugs-address=%s\"" % self.module.get_bugs_enter_url()}
            pot_command = "intltool-update -g '%(domain)s' -p" % {'domain': self.potbase()}
        elif self.module.name == 'damned-lies':
            # special case for d-l, pot file should be generated from running instance dir
            podir = "."
            vcs_path = "./po"
        command = "cd \"%(dir)s\" && %(pot_command)s" % {
            "dir" : podir,
            "pot_command" : pot_command,
            }
        (status, output, errs) = utils.run_shell_command(command, env=env)

        potfile = os.path.join(vcs_path, self.potbase() + ".pot")
        if not os.access(potfile, os.R_OK):
            # Try to get POT file from command output, with path relative to checkout root
            m = re.search('([\w/-]*\.pot)', output)
            if m:
                potfile = os.path.join(current_branch.co_path(), m.group(0))

        if status != utils.STATUS_OK or not os.access(potfile, os.R_OK):
            return "", (("error", ugettext_noop("Error regenerating POT file for %(file)s:\n<pre>%(cmd)s\n%(output)s</pre>")
                                 % {'file': self.potbase(),
                                    'cmd': pot_command,
                                    'output': errs.decode('utf-8')}),
                       )
        else:
            return potfile, ()

    def get_linguas(self, base_path):
        """ Return a linguas dict like this: {'langs':['lang1', lang2], 'error':"Error"} """
        if self.linguas_location:
            # Custom (or no) linguas location
            if self.linguas_location == 'no':
                return {'langs':None, 'error':''}
            elif self.linguas_location.split('/')[-1] == "LINGUAS":
                return utils.read_linguas_file(os.path.join(base_path, self.linguas_location))
            else:
                variable = "ALL_LINGUAS"
                if "#" in self.linguas_location:
                    file_path, variable = self.linguas_location.split("#")
                else:
                    file_path = self.linguas_location
                langs = utils.search_variable_in_file(os.path.join(base_path, file_path), variable)
                return {'langs': langs,
                        'error': ugettext_noop("Entry for this language is not present in %(var)s variable in %(file)s file." % {
                            'var': variable, 'file': file_path})}
        # Standard linguas location
        if self.dtype == 'ui':
            return utils.get_ui_linguas(base_path, os.path.join(base_path, self.directory))
        elif self.dtype == 'doc':
            return utils.get_doc_linguas(base_path, os.path.join(base_path, self.directory))
        else:
            raise ValueError("Domain dtype should be one of 'ui', 'doc'")

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
    # weight is used to sort releases, higher on top, below 0 in archives
    weight   = models.IntegerField(default=0)
    branches = models.ManyToManyField(Branch, through='Category', related_name='releases')

    class Meta:
        db_table = 'release'
        ordering = ('status', '-name')

    def __unicode__(self):
        return self.description

    def get_description(self):
        return _(self.description)

    @classmethod
    def total_by_releases(cls, dtype, releases):
        """ Get summary stats for all languages and 'releases', and return a 'stats' dict with
            each language locale as the key:
            stats{
              'll': {'lang': <language object>,
                     'stats': [percentage for release 1, percentage for release 2, ...],
                     'diff': difference in % between first and last release,
                    }
              'll': ...
            }
        """
        rel_ids = [str(rel.id) for rel in releases]
        LOCALE, NAME, REL_ID, TRANS, FUZZY, UNTRANS = 0, 1, 2, 3, 4, 5
        query = """
            SELECT language.locale, language.name, category.release_id,
                   SUM(stat.translated),
                   SUM(stat.fuzzy),
                   SUM(stat.untranslated)
            FROM statistics AS stat
            LEFT JOIN language
                   ON stat.language_id = language.id
            INNER JOIN domain
                   ON stat.domain_id = domain.id
            INNER JOIN branch
                   ON stat.branch_id = branch.id
            INNER JOIN category
                   ON category.branch_id = branch.id
            WHERE domain.dtype = %%s
              AND category.release_id IN (%s)
            GROUP BY language_id, category.release_id
            ORDER BY language.name""" % (",".join(rel_ids),)
        cursor = connection.cursor()
        cursor.execute(query, (dtype,))
        stats = {}; totals = [0] * len(releases)
        for row in cursor.fetchall():
            if row[LOCALE] and row[LOCALE] not in stats:
                stats[row[LOCALE]] = {'lang': Language.objects.get(locale=row[LOCALE]),
                                      'stats': [0] * len(releases)}
            if row[LOCALE] is None: # POT stats
                totals[rel_ids.index(str(row[REL_ID]))] = row[UNTRANS]
            else:
                stats[row[LOCALE]]['stats'][rel_ids.index(str(row[REL_ID]))] = row[TRANS]
        # Compute percentages
        def perc(x, y): return int(x/y * 100)
        for k in stats.keys():
            stats[k]['stats'] = map(perc, stats[k]['stats'], totals)
            stats[k]['diff'] = stats[k]['stats'][-1] - stats[k]['stats'][0]
        return stats

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
        if settings.DATABASES['default']['ENGINE'].endswith('mysql'):
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
            if row[1] not in stats:
                # Initialize stats dict
                stats[row[1]] = {
                    'lang_name': row[0], 'lang_locale': row[1],
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

        stats = {'doc': Statistics.get_lang_stats_by_type(lang, 'doc', self),
                 'ui':  Statistics.get_lang_stats_by_type(lang, 'ui', self),
                }
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
        unique_together = ('release', 'branch')

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
    # Number of figures in doc templates
    num_figures = models.IntegerField(default=0)

    class Meta:
        db_table = 'statistics'
        verbose_name = "statistics"
        verbose_name_plural = verbose_name
        unique_together = ('branch', 'domain', 'language')

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.figures = None
        self.modname = None
        self.moddescription = None
        self.partial_po = False # True if part of a multiple po module
        self.info_list = []

    def __unicode__(self):
        """ String representation of the object """
        return "%s (%s-%s) %s (%s)" % (self.branch.module.name, self.domain.dtype, self.domain.name,
                                       self.branch.name, self.get_lang())

    def is_fake(self):
        return False

    def is_pot_file(self):
        return self.language is None

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
        if not self.is_pot_file():
            return _("%(lang_name)s (%(lang_locale)s)") % {
                'lang_name': _(self.language.name),
                'lang_locale': self.language.locale
            }
        else:
            return "pot file"

    def module_name(self):
        if not self.modname:
            self.modname = self.branch.module.name
        return self.modname

    def module_description(self):
        if not self.moddescription:
            self.moddescription = self.branch.module.description or self.branch.module.name
        return self.moddescription

    def get_translationstat(self):
        return "%d%%&nbsp;(%d/%d/%d)" % (self.tr_percentage(), self.translated, self.fuzzy, self.untranslated)

    def filename(self, potfile=False):
        if not self.is_pot_file() and not potfile:
            return "%s.%s.%s.po" % (self.domain.potbase(), self.branch.name, self.language.locale)
        else:
            return "%s.%s.pot" % (self.domain.potbase(), self.branch.name)

    def pot_size(self):
        return int(self.translated) + int(self.fuzzy) + int(self.untranslated)

    def pot_text(self):
        """ Return stat table header: 'POT file (n messages) - updated on ??-??-???? tz' """
        pot_size = self.pot_size()
        fig_count = self.fig_count()
        msg_text = ungettext(u"%(count)s message", "%(count)s messages", pot_size) % {'count': pot_size}
        upd_text = _(u"updated on %(date)s") % {
                        # Date format syntax is similar to PHP http://www.php.net/date
                        'date': dateformat.format(self.date, _("Y-m-d g:i a O"))
                        }
        if fig_count:
            fig_text = ungettext(u"%(count)s figure", "%(count)s figures", fig_count) % {'count': fig_count}
            text = _(u"POT file (%(messages)s, %(figures)s) — %(updated)s") % \
                              {'messages': msg_text, 'figures': fig_text, 'updated': upd_text}
        else:
            text = _(u"POT file (%(messages)s) — %(updated)s") % \
                              {'messages': msg_text, 'updated': upd_text}
        return text

    def get_figures(self):
        """ self.figures is a list of dicts:
            [{'path':, 'video':, 'hash':, 'fuzzy':, 'translated':, 'translated_file':}, ...] """
        if self.figures is None and self.domain.dtype == 'doc':
            self.figures = utils.get_fig_stats(self.po_path())
            # something like: "http://git.gnome.org/browse/vinagre / plain / help / %s / %s ?h=master"
            url_model = utils.url_join(self.branch.get_vcs_web_url(), self.branch.img_url_prefix,
                                       self.domain.directory, '%s', '%s') + self.branch.img_url_suffix
            for fig in self.figures:
                fig['orig_remote_url'] = url_model % ('C', fig['path'])
                fig['trans_remote_url'] = url_model % (self.language.locale, fig['path'])
                fig['translated_file'] = False
                if self.language:
                    # Check if a translated figure really exists or if the English one is used
                    if os.path.exists(os.path.join(self.branch.co_path(), self.domain.directory, self.language.locale, fig['path'])):
                        fig['translated_file'] = True
        return self.figures

    def fig_count(self):
        """ If stat of a document type, get the number of figures in the document """
        return self.num_figures

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
        return utils.url_join(self.branch.get_vcs_url(), self.domain.directory)

    def vcs_web_path(self):
        """ Return the Web interface path of file on remote vcs """
        return utils.url_join(self.branch.get_vcs_web_url(), self.domain.directory)

    def po_path(self, potfile=False):
        """ Return path of po file on local filesystem """
        subdir = ""
        if self.domain.dtype == "doc":
            subdir = "docs"
        return os.path.join(settings.POTDIR, self.module_name()+'.'+self.branch.name, subdir, self.filename(potfile))

    def po_url(self, potfile=False):
        """ Return URL of po file, e.g. for downloading the file """
        subdir = ""
        if self.domain.dtype == "doc":
            subdir = "docs/"
        return utils.url_join("/POT/", "%s.%s" % (self.module_name(), self.branch.name), subdir, self.filename(potfile))

    def pot_url(self):
        return self.po_url(potfile=True)

    def set_translation_stats(self, po_path, translated=0, fuzzy=0, untranslated=0, num_figures=0):
        self.translated = translated
        self.fuzzy = fuzzy
        self.untranslated = untranslated
        self.num_figures = num_figures
        self.date = datetime.now()
        self.save()

    def set_errors(self, errors):
        for err in errors:
            self.information_set.add(Information(type=err[0], description=err[1]))

    def informations(self):
        """ Returns information_set, optionally augmented by domain information """
        info_set = [i for i in self.information_set.all()]
        if self.is_pot_file() and self.domain.pot_method:
            # Add a dynamic (ie not saved) Information
            info_set.append(Information(
                statistics  = self,
                type        = 'info',
                description = {
                    'ui' : ugettext_noop("This POT file has not been generated through the standard intltool method."),
                    'doc': ugettext_noop("This POT file has not been generated through the standard gnome-doc-utils method."),
                }.get(self.domain.dtype, ""))
            )
        return info_set

    def most_important_message(self):
        """ Return a message of type 1.'error', or 2.'warn, or 3.'warn """
        error = None
        for e in self.information_set.all():
            if not error or e.type in ('error', 'error-ext') or (e.type in ('warn','warn-ext') and error.type == 'info'):
                error = e
        return error

    @classmethod
    def get_lang_stats_by_type(cls, lang, dtype, release):
        """ Cook statistics for an entire release, a domain type dtype and the language lang.
            Structure of the resulting stats dictionary is as follows:
            stats = {
                'dtype':dtype, # 'ui' or 'doc'
                'total': 0,
                'totaltrans': 0,
                'totalfuzzy': 0,
                'totaluntrans': 0,
                'totaltransperc': 0,
                'totalfuzzyperc': 0,
                'totaluntransperc': 0,
                'categs': {
                    <categname>: {
                        'catname': <catname>, # translated category name (see CATEGORY_CHOICES)
                        'cattotal': 0,
                        'cattrans': 0,
                        'catfuzzy': 0,
                        'catuntrans': 0,
                        'cattransperc': 0,
                        'modules': { # This dict is converted to a sorted list at the end of stats computation
                            <modname>: {
                                <branchname>:
                                    [(<domname>, <stat>), ...], # List of tuples (domain name, Statistics object)
                                           # First element is a placeholder for a FakeStatistics object
                                           # only used for summary if module has more than 1 domain
                                }
                            }
                        }
                    }
                },
                'all_errors':[]
            }
        """
        from vertimus.models import StateDb, ActionDb # import here to prevent a circular dependency

        stats = {'dtype':dtype, 'totaltrans':0, 'totalfuzzy':0, 'totaluntrans':0,
                 'totaltransperc': 0, 'totalfuzzyperc': 0, 'totaluntransperc': 0,
                 'categs':{}, 'all_errors':[]}
        # Sorted by module to allow grouping ('fake' stats)
        pot_stats = Statistics.objects.select_related('domain', 'branch__module')
        if release:
            pot_stats = pot_stats.extra(select={'categ_name': "category.name"}).filter(language=None, branch__releases=release, domain__dtype=dtype).order_by('branch__module__id')
        else:
            pot_stats = pot_stats.filter(language=None, domain__dtype=dtype).order_by('branch__module__id')

        tr_stats = Statistics.objects.select_related('domain', 'language', 'branch__module')
        if release:
            tr_stats = tr_stats.filter(language=lang, branch__releases=release, domain__dtype=dtype).order_by('branch__module__id')
        else:
            tr_stats = tr_stats.filter(language=lang, domain__dtype=dtype).order_by('branch__module__id')
        tr_stats_dict = dict([("%d-%d" % (st.branch.id, st.domain.id),st) for st in tr_stats])

        infos_dict = Information.get_info_dict(lang)

        # Prepare StateDb objects in a dict (with "branch_id-domain_id" as key), to save database queries later
        vt_states = StateDb.objects.select_related('branch','domain')
        if release:
            vt_states = vt_states.filter(language=lang, branch__releases=release, domain__dtype=dtype)
        else:
            vt_states = vt_states.filter(language=lang, domain__dtype=dtype)
        vt_states_dict = dict([("%d-%d" % (vt.branch.id, vt.domain.id),vt) for vt in vt_states])

        # Get comments from last action of StateDb objects
        actions = ActionDb.objects.filter(state_db__in=vt_states, comment__isnull=False).order_by('created')
        actions_dict = dict([(act.state_db_id, act) for act in actions])
        for vt_state in vt_states_dict.values():
            if vt_state.id in actions_dict:
                vt_state.last_comment = actions_dict[vt_state.id].comment

        for stat in pot_stats:
            categdescr = "default"
            if release:
                categdescr = stat.categ_name
            domname = _(stat.domain.description)
            branchname = stat.branch.name
            modname = stat.branch.module.name
            if categdescr not in stats['categs']:
                stats['categs'][categdescr] = {'cattrans':0, 'catfuzzy':0, 'catuntrans':0,
                                               'cattransperc':0, 'modules':{}}
            # Try to get translated stat, else stick with POT stat
            br_dom_key = "%d-%d" % (stat.branch.id, stat.domain.id)
            if br_dom_key in tr_stats_dict:
                stat = tr_stats_dict[br_dom_key]
            # Match stat with error list
            if stat.id in infos_dict:
                stat.info_list = infos_dict[stat.id]
                stats['all_errors'].extend(stat.info_list)

            # Search if a state exists for this statistic
            if br_dom_key in vt_states_dict:
                stat.state = vt_states_dict[br_dom_key]

            stats['totaltrans'] += stat.translated
            stats['totalfuzzy'] += stat.fuzzy
            stats['totaluntrans'] += stat.untranslated
            stats['categs'][categdescr]['cattrans'] += stat.translated
            stats['categs'][categdescr]['catfuzzy'] += stat.fuzzy
            stats['categs'][categdescr]['catuntrans'] += stat.untranslated
            if modname not in stats['categs'][categdescr]['modules']:
                # first element is a placeholder for a fake stat
                stats['categs'][categdescr]['modules'][modname] = {branchname:[[' fake', None], (domname, stat)]}
            elif branchname not in stats['categs'][categdescr]['modules'][modname]:
                # first element is a placeholder for a fake stat
                stats['categs'][categdescr]['modules'][modname][branchname] = [[' fake', None], (domname, stat)]
            else:
                # Here we add the 2nd or more stat to the same module-branch
                if len(stats['categs'][categdescr]['modules'][modname][branchname]) == 2:
                    # Create a fake statistics object for module summary
                    stats['categs'][categdescr]['modules'][modname][branchname][0][1] = FakeStatistics(stat.domain.module, stat.branch, dtype)
                    stats['categs'][categdescr]['modules'][modname][branchname][0][1].trans(stats['categs'][categdescr]['modules'][modname][branchname][1][1])
                stats['categs'][categdescr]['modules'][modname][branchname].append((domname, stat))
                stats['categs'][categdescr]['modules'][modname][branchname][0][1].trans(stat)

        # Compute percentages and sorting
        stats['total'] = stats['totaltrans'] + stats['totalfuzzy'] + stats['totaluntrans']
        if stats['total'] > 0:
            stats['totaltransperc'] = int(100*stats['totaltrans']/stats['total'])
            stats['totalfuzzyperc'] = int(100*stats['totalfuzzy']/stats['total'])
            stats['totaluntransperc'] = int(100*stats['totaluntrans']/stats['total'])
        for key, categ in stats['categs'].items():
            categ['catname'] = Category.get_cat_name(key)
            categ['cattotal'] = categ['cattrans'] + categ['catfuzzy'] + categ['catuntrans']
            if categ['cattotal'] > 0:
                categ['cattransperc'] = int(100*categ['cattrans']/categ['cattotal'])
            # Sort modules
            mods = [[name,mod] for name, mod in categ['modules'].items()]
            mods.sort()
            categ['modules'] = mods
            # Sort domains
            for mod in categ['modules']:
                for branch, doms in mod[1].items():
                    doms.sort()
        # Sort errors
        stats['all_errors'].sort()
        return stats

class FakeStatistics(object):
    """ This is a fake statistics class where a summary value is needed for a multi-domain module
        This is used in get_lang_stats for the language-release-stats template """
    def __init__(self, module, branch, dtype, lang=None):
        self.module = module
        self.branch = branch
        self.domain = module.domain_set.filter(dtype=dtype)[0]
        self.language = lang
        self.translated = 0
        self.fuzzy = 0
        self.untranslated = 0
        self.partial_po = False
        self.figures = None

    def trans(self, stat):
        self.translated += stat.translated
        self.fuzzy += stat.fuzzy
        self.untranslated += stat.untranslated
        stat.partial_po = True

    def is_fake(self):
        return True

    def get_lang(self):
        if self.language:
            return _("%(lang_name)s (%(lang_locale)s)") % {
                'lang_name': _(self.language.name),
                'lang_locale': self.language.locale
            }
        else:
            return "pot file"

    def get_translationstat(self):
        return "%d%%&nbsp;(%d/%d/%d)" % (self.tr_percentage(), self.translated, self.fuzzy, self.untranslated)

    def fig_stats(self):
        stats = {'fuzzy':0, 'translated':0, 'untranslated':0, 'total':0, 'prc':0}
        for fig in self.get_figures():
            stats['total'] += 1
            stats['untranslated'] += 1
        return stats

    def get_figures(self):
        """ self.figures is a list of dicts:
            [{'path':, 'hash':, 'fuzzy':, 'translated':, 'translated_file':}, ...] """
        if self.figures is None and self.domain.dtype == 'doc':
            self.figures = utils.get_fig_stats(self.po_path())
            # something like: "http://git.gnome.org/browse/vinagre / plain / help / %s / %s ?h=master"
            url_model = utils.url_join(self.branch.get_vcs_web_url(), self.branch.img_url_prefix,
                                       self.domain.directory, '%s', '%s') + self.branch.img_url_suffix
            for fig in self.figures:
                fig['orig_remote_url'] = url_model % ('C', fig['path'])
                fig['trans_remote_url'] = url_model % (self.language.locale, fig['path'])
                fig['translated_file'] = False
                if self.language:
                    # Check if a translated figure really exists or if the English one is used
                    if os.path.exists(os.path.join(self.branch.co_path(), self.domain.directory, self.language.locale, fig['path'])):
                        fig['translated_file'] = True
        return self.figures

    def po_path(self):
        """ Return path of pot file on local filesystem """
        subdir = ""
        if self.domain.dtype == "doc":
            subdir = "docs"
        filename = "%s.%s.pot" % (self.domain.potbase(), self.branch.name)
        return os.path.join(settings.POTDIR, self.module_name()+'.'+self.branch.name, subdir, filename)

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
    def most_important_message(self):
        return None

class StatisticsArchived(models.Model):
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
        db_table = 'statistics_archived'

INFORMATION_TYPE_CHOICES = (
    ('info', 'Information'),
    ('warn','Warning'),
    ('error','Error'),
    # Type of warning/error external to po file itself (LINGUAS, images, etc.)
    # po files containing these are always rechecked
    ('warn-ext','Warning (external)'),
    ('error-ext','Error (external)')
)
class Information(models.Model):
    statistics = models.ForeignKey('Statistics')
    # Priority of a stats message
    type = models.CharField(max_length=10, choices=INFORMATION_TYPE_CHOICES)
    description = models.TextField()

    class Meta:
        db_table = 'information'

    @classmethod
    def get_info_dict(cls, lang):
        """ Return a dict (of lists) with all Information objects for a lang, with statistics_id as the key
            Used for caching and preventing db access when requesting these objects for a long list of stats """
        info_dict = {}
        for info in Information.objects.filter(statistics__language=lang):
            if info.statistics_id in info_dict:
                info_dict[info.statistics_id].append(info)
            else:
                info_dict[info.statistics_id] = [info]
        return info_dict

    def __cmp__(self, other):
        return cmp(self.statistics.module_name(), other.statistics.module_name())

    def get_icon(self):
        return "%simg/%s.png" % (settings.MEDIA_URL, self.type.split("-")[0])

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

class InformationArchived(models.Model):
    statistics = models.ForeignKey('StatisticsArchived')
    # Priority of a stats message
    type = models.CharField(max_length=10, choices=INFORMATION_TYPE_CHOICES)
    description = models.TextField()

    class Meta:
        db_table = 'information_archived'
