# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2009 Claude Paroz <claude@2xlibre.net>
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
from django.conf import settings
from stats.models import Module, Domain, Branch, Category, Release, Statistics, Information
from languages.models import Language

class ModuleTestCase(TestCase):
    def __init__(self, name):
        TestCase.__init__(self, name)
        # Delete the checkout if it exists prior to running the test suite
        path = os.path.join(settings.SCRATCHDIR, 'git', 'gnome-hello')
        if os.access(path, os.X_OK):
            shutil.rmtree(path)

    def setUp(self):
        # TODO: load bulk data from fixtures
        Branch.checkout_on_creation = False
        self.mod = Module(name="gnome-hello",
                  bugs_base="http://bugzilla.gnome.org",
                  bugs_product="test", # This product really exists
                  bugs_component="test",
                  vcs_type="git",
                  vcs_root="git://git.gnome.org/gnome-hello",
                  vcs_web="http://git.gnome.org/cgit/gnome-hello/")
        self.mod.save()
        dom = Domain(module=self.mod, name='po', description='UI Translations', dtype='ui', directory='po')
        dom.save()
        dom = Domain(module=self.mod, name='help', description='User Guide', dtype='doc', directory='help')
        dom.save()

        self.b = Branch(name='master', module=self.mod)
        self.b.save(update_statistics=False)

        self.rel = Release(name='gnome-2-24', status='official',
                      description='GNOME 2.24 (stable)',
                      string_frozen=True)
        self.rel.save()

        self.cat = Category(release=self.rel, branch=self.b, name='desktop')
        self.cat.save()

    def testModuleFunctions(self):
        self.assertEquals(self.mod.get_description(), 'gnome-hello')

    def testBranchFunctions(self):
        self.assertTrue(self.b.is_head())
        self.assertEquals(self.b.get_vcs_url(), "git://git.gnome.org/gnome-hello")
        self.assertEquals(self.b.get_vcs_web_url(), "http://git.gnome.org/cgit/gnome-hello/")

    def testBranchStats(self):
        # Check stats
        self.b.update_stats(force=True)
        fr_po_stat = Statistics.objects.get(branch=self.b, domain__name='po', language__locale='fr')
        self.assertEquals(fr_po_stat.translated, 47)
        fr_doc_stat = Statistics.objects.get(branch=self.b, domain__name='help', language__locale='fr')
        self.assertEquals(fr_doc_stat.translated, 22)

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

    def testStringFrozenMail(self):
        """ String change for a module of a string_frozen release should generate a message """
        mail.outbox = []
        self.rel.string_frozen = True
        self.rel.save()

        # Create a new file with translation
        new_file_path = os.path.join(self.b.co_path(), "dummy_file.py")
        new_string = "Dummy string for D-L tests"
        f = open(new_file_path,'w')
        f.write("a = _('%s')\n" % new_string)
        f.close()
        # Add the new file to POTFILES.in
        f = open(os.path.join(self.b.co_path(), "po", "POTFILES.in"), 'a')
        f.write("dummy_file.py\n")
        f.close()
        # Regenerate stats (mail should be sent)
        self.b.update_stats(force=False, checkout=False)
        # Assertions
        self.assertEquals(len(mail.outbox), 1);
        self.assertEquals(mail.outbox[0].subject, "String additions to 'gnome-hello.master'")
        self.assertTrue(mail.outbox[0].message().as_string().find(new_string)>-1)

    def testIdenticalFigureWarning(self):
        """ Detect warning if translated figure is identical to original figure """
        self.b.checkout()
        orig_figure = os.path.join(self.b.co_path(), "help", "C", "figures", "gnome-hello.png")
        shutil.copy(orig_figure, os.path.join(self.b.co_path(), "help", "fr", "figures", "gnome-hello.png"))
        self.b.update_stats(force=True, checkout=False)
        doc_stat = Statistics.objects.get(branch=self.b, domain__name='help', language__locale='fr')
        warn_infos = Information.objects.filter(statistics=doc_stat, type='warn-ext')
        self.assertEquals(len(warn_infos), 1);
        ui_stat = Statistics.objects.get(branch=self.b, domain__name='po', language__locale='fr')
        self.assertEquals(ui_stat.po_url(), u"/POT/gnome-hello.master/gnome-hello.master.fr.po");
        self.assertEquals(ui_stat.pot_url(), u"/POT/gnome-hello.master/gnome-hello.master.pot");
        self.assertEquals(doc_stat.po_url(), u"/POT/gnome-hello.master/docs/gnome-hello-help.master.fr.po");

    def testFigureURLs(self):
        """ Test if figure urls are properly constructed """
        self.b.update_stats(force=True)
        stat = Statistics.objects.get(branch=self.b, domain__dtype='doc', language__locale='fr')
        figs = stat.get_figures()
        self.assertEquals(figs[0]['orig_remote_url'], 'http://git.gnome.org/cgit/gnome-hello/plain/help/C/figures/gnome-hello.png?h=master')
        self.assertEquals(figs[0]['trans_remote_url'], 'http://git.gnome.org/cgit/gnome-hello/plain/help/fr/figures/gnome-hello.png?h=master')

    def testCreateUnexistingBranch(self):
        """ Try to create a non-existing branch """
        Branch.checkout_on_creation = True
        branch = Branch(name="trunk2",
                        module = self.mod)
        self.assertRaises(ValueError, branch.save)
        Branch.checkout_on_creation = False

    def testDynamicPO(self):
        """ Test the creation of a blank po file for a new language """
        lang = Language(name="Tamil", locale="ta")
        lang.save()
        self.b.update_stats(force=True) # At least POT stats needed
        c = Client()
        response = c.get('/module/po/gnome-hello.po.master.ta.po')
        self.assertContains(response, """# Tamil translation for gnome-hello.
# Copyright (C) %s gnome-hello's COPYRIGHT HOLDER
# This file is distributed under the same license as the gnome-hello package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.""" % date.today().year)
        self.assertContains(response, "Language-Team: Tamil <ta@li.org>")
