# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>
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

from django.test import TestCase
from people.models import Person
from teams.models import Team
from languages.models import Language
from stats.models import Module, Branch, Release, Category, Domain
from vertimus.models import *

class VtmActionTests(TestCase):

    def setUp(self):
        self.p = Person(first_name='John', last_name='Lennon',
            email='jlennon@beatles.com')
        self.p.save()

        self.t = Team(name='fr', description='French', coordinator=self.p)
        self.t.save()

        self.l = Language(name='french', locale='fr', team=self.t)
        self.l.save()

        self.m = Module(name='gedit', description='GNOME Editor',
            bugs_base="http://bugzilla.gnome.org/",
            bugs_product='gedit', bugs_component='general',
            vcs_type='svn', vcs_root="http://svn.gnome.org/svn",
            vcs_web="http://svn.gnome.org/viewvc/gedit")
        self.m.save()

        self.b = Branch(name='gnome-2-24', module=self.m) 
        self.b.save()

        self.r = Release(name='gnome-2-24', status='official',
            description='GNOME 2.24 (stable)',
            string_frozen=True)
        self.r.save()

        self.c = Category(release=self.r, branch=self.b, name='desktop')
        self.c.save()

        self.d = Domain(module=self.m, name='po',
            description='UI translations',
            dtype='ui', directory='po')
        self.d.save()
        
    def tearDown(self):
        self.d.delete()
        self.c.delete()
        self.r.delete()
        self.b.delete()
        self.m.delete()
        self.l.delete()
        self.t.delete()
        self.p.delete()

    def test_action_wc(self):
        a = VtmActionWC()
        self.assertEquals(a.code, 'WC')
        s_next = a.apply(self.b, self.d, self.l, self.p, 'Hi!')
        self.assertEquals(s_next, None)
        
    def test_action_rt(self):
        a = VtmActionRT()
        self.assertEquals(a.code, 'RT')
        s_next = a.apply(self.b, self.d, self.l, self.p, "Let's go!")
        self.assertEquals(s_next.get_code(), 'Translating')

    def test_action_ut(self):
        # Only the person who have reserved the translation is able to
        # upload the new one
        a = VtmActionRT()
        s_current = a.apply(self.b, self.d, self.l, self.p, "Let's go!")
        a = VtmActionUT()
        self.assertEquals(a.code, 'UT')
        s_next = s_current.apply_action(a, self.b, self.d, self.l, self.p, 'Just updated', 'fr.po')
        self.assertEquals(s_next.get_code(), 'Translated')

    def test_state_committed_action_wc(self):
        s_current = VtmStateCommitted()
        a_wc = None
        # Writing a comment is always a possible action
        for action in s_current.get_actions(self.b, self.d, self.l, self.p):
            if isinstance(action, VtmActionWC):
                a_wc = action
                break
        self.assertNotEquals(a_wc, None)
        s_next = s_current.apply_action(a_wc, self.b, self.d, self.l, self.p, 'My comment')
        self.assertEquals(s_current, s_next)

        

        
        
