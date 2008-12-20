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

import unittest
import threading
from stats.models import Module, Domain, Branch, Statistics

class ModuleTestCase(unittest.TestCase):
    def setUp(self):
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
            
    def testModuleFunctions(self):
        self.assertEquals(self.mod.get_description(), 'gnome-hello')
        
    def testBranch(self):
        # Create branch (include checkout)
        branch = Branch(name="trunk",
                        module = self.mod)
        branch.save()
        
        self.assertEquals(branch.is_head(), True)
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
        
        # Delete branch to remove the repo checkout
        branch.delete()
        
        # TODO: Try to create a non-existing branch...
