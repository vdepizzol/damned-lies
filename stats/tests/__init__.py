# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2011 Claude Paroz <claude@2xlibre.net>
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

import os, shutil
from datetime import date
from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings

from stats.models import Module, Domain, Branch, Category, Release, Statistics, FakeLangStatistics, Information
from stats.utils import check_program_presence, run_shell_command
from languages.models import Language

from fixture_factory import *

def test_scratchdir(test_func):
    """ Decorator to temporarily use the scratchdir inside the test directory """
    def decorator(self):
        old_SCRATCHDIR = settings.SCRATCHDIR
        old_POTDIR = settings.POTDIR
        settings.SCRATCHDIR = os.path.dirname(os.path.abspath(__file__))
        settings.POTDIR = os.path.join(settings.SCRATCHDIR, "POT")
        test_func(self)
        settings.SCRATCHDIR = old_SCRATCHDIR
        settings.POTDIR = old_POTDIR
    return decorator


class ModuleTestCase(TestCase):
    fixtures = ['sample_data.json']
    SYS_DEPENDENCIES = (
        ('gettext', 'msgfmt'),
        ('intltool', 'intltool-update'),
        ('gnome-doc-utils', 'xml2po'),
    )
    def __init__(self, name):
        TestCase.__init__(self, name)
        for package, prog in self.SYS_DEPENDENCIES:
            if not check_program_presence(prog):
                raise Exception("You are missing a required system package needed by Damned Lies (%s)" % package)
        # Delete the checkout if it exists prior to running the test suite
        self.co_path = os.path.join(settings.SCRATCHDIR, 'git', 'gnome-hello')
        if os.access(self.co_path, os.X_OK):
            shutil.rmtree(self.co_path)

    def setUp(self):
        Branch.checkout_on_creation = False
        self.mod = Module.objects.get(name="gnome-hello")
        self.branch = self.mod.branch_set.get(name="master")

    def tearDown(self):
        if os.access(self.co_path, os.X_OK):
            command = "cd \"%s\" && git reset --hard origin/master" % self.co_path
            run_shell_command(command, raise_on_error=True)

    def testModuleFunctions(self):
        self.assertEqual(self.mod.get_description(), 'gnome-hello')

    def testBranchFunctions(self):
        self.assertTrue(self.branch.is_head())
        self.assertEqual(self.branch.get_vcs_url(), "git://git.gnome.org/gnome-hello")
        self.assertEqual(self.branch.get_vcs_web_url(), "http://git.gnome.org/browse/gnome-hello/")

    def testBranchStats(self):
        lang = Language.objects.create(name='xxx', locale='xxx')
        ghost_stat = Statistics.objects.create(branch=self.branch, domain=self.mod.domain_set.get(name='po'), language=lang)
        # Check stats
        self.branch.update_stats(force=True)
        fr_po_stat = Statistics.objects.get(branch=self.branch, domain__name='po', language__locale='fr')
        self.assertEqual(fr_po_stat.translated(), 44)
        fr_doc_stat = Statistics.objects.get(branch=self.branch, domain__name='help', language__locale='fr')
        self.assertEqual(fr_doc_stat.translated(), 16)
        self.assertEqual(fr_po_stat.po_url(), u"/POT/gnome-hello.master/gnome-hello.master.fr.po")
        self.assertEqual(fr_po_stat.pot_url(), u"/POT/gnome-hello.master/gnome-hello.master.pot")
        self.assertEqual(fr_doc_stat.po_url(), u"/POT/gnome-hello.master/docs/gnome-hello-help.master.fr.po")
        self.assertRaises(Statistics.DoesNotExist, Statistics.objects.get, pk=ghost_stat.pk)

    def testCreateAndDeleteBranch(self):
        Branch.checkout_on_creation = True
        # Create branch (include checkout)
        branch = Branch(name="gnome-hello-1-4", module = self.mod)
        branch.save()
        # Delete the branch (removing the repo checkout in the file system)
        checkout_path = branch.co_path()
        branch = Branch.objects.get(name="gnome-hello-1-4", module = self.mod)
        branch.delete()
        # FIXME: deleting a git branch doesn't delete the repo
        #self.assertFalse(os.access(checkout_path, os.F_OK))

    def testBranchSorting(self):
        b1 = Branch(name='a-branch', module=self.mod)
        b1.save(update_statistics=False)
        b2 = Branch(name='p-branch', module=self.mod)
        b2.save(update_statistics=False)
        self.assertEqual([b.name for b in sorted(self.mod.branch_set.all())], ['master','p-branch','a-branch'])
        b1.weight = -1
        b1.save(update_statistics=False)
        self.assertEqual([b.name for b in sorted(self.mod.branch_set.all())], ['master','a-branch','p-branch'])

    def testStringFrozenMail(self):
        """ String change for a module of a string_frozen release should generate a message """
        mail.outbox = []
        self.branch.update_stats(force=False)

        # Create a new file with translation
        new_file_path = os.path.join(self.branch.co_path(), "dummy_file.py")
        new_string = "Dummy string for D-L tests"
        f = open(new_file_path,'w')
        f.write("a = _('%s')\n" % new_string)
        f.close()
        # Add the new file to POTFILES.in
        f = open(os.path.join(self.branch.co_path(), "po", "POTFILES.in"), 'a')
        f.write("dummy_file.py\n")
        f.close()
        # Regenerate stats (mail should be sent)
        self.branch.update_stats(force=False, checkout=False)
        # Assertions
        self.assertEqual(len(mail.outbox), 1);
        self.assertEqual(mail.outbox[0].subject, "String additions to 'gnome-hello.master'")
        self.assertTrue(mail.outbox[0].message().as_string().find(new_string)>-1)

    def testReadFileVariable(self):
        from stats.utils import search_variable_in_file
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "help_docbook", "Makefile.am")
        var_content = search_variable_in_file(file_path, "DOC_INCLUDES")
        self.assertEqual(var_content.split(), ['rnusers.xml', 'rnlookingforward.xml', '$(NULL)'])

    def testGenerateDocPotfile(self):
        from stats.utils import generate_doc_pot_file, get_fig_stats, DocFormat
        # Docbook-style help
        help_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "help_docbook")
        potfile, errs, doc_format = generate_doc_pot_file(help_path, 'release-notes', 'release-notes')
        pot_path = os.path.join(help_path, "C", "release-notes.pot")
        self.assertTrue(os.access(pot_path, os.R_OK))
        res = get_fig_stats(pot_path, doc_format=doc_format)
        self.assertEqual(len(res), 1)
        os.remove(pot_path)
        # Mallard-style help (with itstool)
        pot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "help_mallard", "gnome-help-itstool.pot")
        res = get_fig_stats(pot_path, doc_format=DocFormat(True, True))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]['path'], "figures/gnome.png")

    def testHttpPot(self):
        dom = Domain.objects.create(
            module=self.mod, name='http-po',
            description='UI Translations', dtype='ui',
            pot_method='http://l10n.gnome.org/POT/damned-lies.master/damned-lies.master.pot')
        self.branch.checkout()
        potfile, errs = dom.generate_pot_file(self.branch)
        self.assertTrue(os.path.exists(potfile))

    def testCreateUnexistingBranch(self):
        """ Try to create a non-existing branch """
        Branch.checkout_on_creation = True
        branch = Branch(name="trunk2",
                        module = self.mod)
        self.assertRaises(ValidationError, branch.clean)

    def testDynamicPO(self):
        """ Test the creation of a blank po file for a new language """
        lang = Language.objects.create(name="Tamil", locale="ta")
        self.branch.update_stats(force=False) # At least POT stats needed
        response = self.client.get('/module/po/gnome-hello/po/master/ta.po')
        self.assertContains(response, """# Tamil translation for gnome-hello.
# Copyright (C) %s gnome-hello's COPYRIGHT HOLDER
# This file is distributed under the same license as the gnome-hello package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.""" % date.today().year)
        self.assertContains(response, "Language-Team: Tamil <ta@li.org>")
        response = self.client.get('/module/po/gnome-hello/po/master/ta-reduced.po')
        self.assertContains(response, """# Tamil translation for gnome-hello.""")

    @test_scratchdir
    def testBranchFileChanged(self):
        self.assertTrue(self.mod.get_head_branch().file_changed("gnome-hello.doap"))
        self.assertFalse(self.mod.get_head_branch().file_changed("gnome-hello.doap"))

    @test_scratchdir
    def testUpdateMaintainersFromDoapFile(self):
        from stats.doap import update_doap_infos
        from people.models import Person
        # Add a maintainer which will be removed
        pers = Person(username="toto")
        pers.save()
        self.mod.maintainers.add(pers)
        update_doap_infos(self.mod)
        self.assertEqual(self.mod.maintainers.count(), 6)
        claude = self.mod.maintainers.get(email='claude@2xlibre.net')
        self.assertEqual(claude.username, 'claudep')

    @test_scratchdir
    def testUpdateDoapInfos(self):
        from stats.doap import update_doap_infos
        update_doap_infos(self.mod)
        self.assertEqual(self.mod.homepage, "http://git.gnome.org/browse/gnome-hello")


class StatisticsTests(TestCase):
    fixtures = ['sample_data.json']
    def testTotalStatsForLang(self):
        rel  = Release.objects.get(name="gnome-2-30")
        total_for_lang = rel.total_for_lang(Language.objects.get(locale='fr'))
        self.assertEqual(total_for_lang['ui']['total'], total_for_lang['ui_part']['total'])
        self.assertTrue(total_for_lang['ui']['untranslated'] == total_for_lang['ui_part']['untranslated'] == 0)
        total_for_lang = rel.total_for_lang(Language.objects.get(locale='bem'))
        self.assertEqual(total_for_lang['ui']['total']-8, total_for_lang['ui_part']['total'])
        self.assertEqual(total_for_lang['ui']['untranslated'], 183)
        self.assertEqual(total_for_lang['ui_part']['untranslated'], 175)

    def testStatsLinks(self):
        pot_stats = Statistics.objects.get(
            branch__module__name='zenity', branch__name='gnome-2-30',
            domain__name='po', language__isnull=True)
        self.assertEqual(pot_stats.po_url(), "/POT/zenity.gnome-2-30/zenity.gnome-2-30.pot")
        stats = Statistics.objects.get(
            branch__module__name='zenity', branch__name='gnome-2-30',
            domain__name='po', language__locale='it')
        self.assertEqual(stats.po_url(), "/POT/zenity.gnome-2-30/zenity.gnome-2-30.it.po")
        self.assertEqual(stats.po_url(reduced=True), "/POT/zenity.gnome-2-30/zenity.gnome-2-30.it.reduced.po")
        # Same for a fake stats
        stats = FakeLangStatistics(pot_stats, Language.objects.get(locale='bem'))
        self.assertEqual(stats.po_url(), "/module/po/zenity.po.gnome-2-30.bem.po")
        self.assertEqual(stats.po_url(reduced=True), "/module/po/zenity.po.gnome-2-30.bem-reduced.po")

    def testSetTranslationStats(self):
        from vertimus.models import State, StateTranslating
        # Get a stat that has full_po and part_po
        stat = Statistics.objects.get(branch__module__name='zenity', branch__name='gnome-2-30', language__locale='it', domain__dtype='ui')
        pers = Person.objects.create(username="toto")
        state = StateTranslating.objects.create(branch=stat.branch, domain=stat.domain, language=stat.language, person=pers)
        # Mark file completely translated
        self.assertNotEqual(stat.part_po, stat.full_po)
        stat.set_translation_stats('dummy', 136, 0, 0)
        self.assertEqual(stat.part_po, stat.full_po)
        # Check state is still translating
        state = State.objects.filter(branch=stat.branch, domain=stat.domain, language=stat.language)
        self.assertEqual(len(state), 1)
        self.assertTrue(isinstance(state[0], StateTranslating))

class FigureTests(TestCase):
    fixtures = ['sample_data.json']
    def testFigureView(self):
        url = reverse('stats.views.docimages', args=['gnome-hello', 'help', 'master', 'fr'])
        response = self.client.get(url)
        self.assertContains(response, "gnome-hello-new.png")
        # Same for a non-existing language
        Language.objects.create(name='Afrikaans', locale='af')
        url = reverse('stats.views.docimages', args=['gnome-hello', 'help', 'master', 'af'])
        response = self.client.get(url)
        self.assertContains(response, "gnome-hello-new.png")

    def testFigureURLs(self):
        """ Test if figure urls are properly constructed """
        stat = Statistics.objects.get(branch__module__name='gnome-hello', branch__name='master', domain__dtype='doc', language__locale='fr')
        figs = stat.get_figures()
        self.assertEqual(figs[0]['orig_remote_url'], 'http://git.gnome.org/browse/gnome-hello/plain/help/C/figures/gnome-hello-new.png?h=master')
        self.assertFalse('trans_remote_url' in figs[0])

    @test_scratchdir
    def testIdenticalFigureWarning(self):
        """ Detect warning if translated figure is identical to original figure """
        from stats.utils import check_identical_figures
        branch = Branch.objects.get(module__name='gnome-hello', name='master')
        doc_stat = Statistics.objects.get(branch=branch, domain__name='help', language__locale='fr')
        errs = check_identical_figures(doc_stat.get_figures(), os.path.join(branch.co_path(), 'help'), 'fr')
        self.assertEqual(len(errs), 1)
        self.assertTrue(errs[0][1].startswith("Figures should not be copied"))
