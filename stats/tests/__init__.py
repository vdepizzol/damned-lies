# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Claude Paroz <claude@2xlibre.net>
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

import os, unittest
import threading
from django.core import mail
from stats.models import Module, Domain, Branch, Category, Release, Statistics

class ModuleTestCase(unittest.TestCase):
    def setUp(self):
        # TODO: load bulk data from fixtures 
        self.mod = Module(name="gnome-hello",
                          bugs_base="http://bugzilla.gnome.org",
                          bugs_product="test", # This product really exists
                          bugs_component="test",
                          vcs_type="svn",
                          vcs_root="http://svn.gnome.org/svn",
                          vcs_web="http://svn.gnome.org/viewvc/gnome-hello")
        self.mod.save()
        dom = Domain(module=self.mod, name='po', description='UI Translations', dtype='ui', directory='po')
        dom.save()
        dom = Domain(module=self.mod, name='help', description='User Guide', dtype='doc', directory='help')
        dom.save()
        self.rel = Release(name='gnome-2-24', status='official',
                      description='GNOME 2.24 (stable)',
                      string_frozen=True)
        self.rel.save()
    
    def testModuleFunctions(self):
        self.assertEquals(self.mod.get_description(), 'gnome-hello')
        
    def testCreateAndDeleteBranch(self):
        # Create branch (include checkout)
        branch = Branch(name="trunk",
                        module = self.mod)
        branch.save()
        self.assertTrue(branch.is_head())
        self.assertEquals(branch.get_vcs_url(), "http://svn.gnome.org/svn/gnome-hello/trunk")
        self.assertEquals(branch.get_vcs_web_url(), "http://svn.gnome.org/viewvc/gnome-hello/trunk")

        # save() launch update_stats in a separate thread, wait for the thread to end before pursuing the tests
        for th in threading.enumerate():
            if th != threading.currentThread():
                print "Waiting for thread %s to finish" % th.getName()
                th.join()
        
        # Check stats
        fr_po_stat = Statistics.objects.get(branch=branch, domain__name='po', language__locale='fr')
        self.assertEquals(fr_po_stat.translated, 40)
        fr_doc_stat = Statistics.objects.get(branch=branch, domain__name='help', language__locale='fr')
        self.assertEquals(fr_doc_stat.translated, 36)

        # Link gnome-hello trunk to a string_frozen release
        cat = Category(release=self.rel, branch=branch, name='desktop')
        cat.save()
                
        # Create a new file with translation
        new_file_path = os.path.join(branch.co_path(), "dummy_file.h")
        new_string = "Dummy string for D-L tests"
        f = open(new_file_path,'w')
        f.write("a = _('%s')" % new_string)
        f.close()
        # Add the new file to POTFILES.in
        f = open(os.path.join(branch.co_path(), "po", "POTFILES.in"), 'a')
        f.write("dummy_file.h")
        f.close()
        # Regenerate stats (mail should be sent)
        branch.update_stats(force=False)
        # Assertions
        self.assertEquals(len(mail.outbox), 1);
        self.assertEquals(mail.outbox[0].subject, "String additions to '%s'")
        self.assertTrue(new_string in mail.outbox[0].message)

        # Delete the branch (removing the repo checkout in the file system)
        checkout_path = branch.co_path()
        branch = Branch.objects.get(name="trunk", module = self.mod)
        branch.delete()
        self.assertFalse(os.access(checkout_path, os.F_OK))
     
    def testCreateUnexistingBranch(self):
        """ Try to create a non-existing branch """
        branch = Branch(name="trunk2",
                        module = self.mod)
        self.assertRaises(ValueError, branch.save)

