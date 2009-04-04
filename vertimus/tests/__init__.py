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

import os

from django.test import TestCase
from django.core.files.base import File, ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict
from django.conf import settings

from people.models import Person
from teams.models import Team, Role
from languages.models import Language
from stats.models import Module, Branch, Release, Category, Domain
from vertimus.models import *
from vertimus.forms import ActionForm

class VertimusTests(TestCase):

    def setUp(self):
        self.pn = Person(first_name='John', last_name='Nothing',
            email='jn@devnull.com', username= 'jn')
        self.pn.save()
        
        self.pt = Person(first_name='John', last_name='Translator',
            email='jt@tf1.com', username= 'jt')
        self.pt.save()

        self.pr = Person(first_name='John', last_name='Reviewer',
            email='jr@csa.com', username= 'jr')
        self.pr.save()

        self.pc = Person(first_name='John', last_name='Committer',
            email='jc@alinsudesonpleingre.fr', username= 'jc')
        self.pc.save()

        self.pcoo = Person(first_name='John', last_name='Coordinator',
            email='jcoo@imthebigboss.fr', username= 'jcoo')
        self.pcoo.save()

        self.t = Team(name='fr', description='French')
        self.t.save()

        self.role = Role(team=self.t, person=self.pt)
        self.role.save()

        self.role = Role(team=self.t, person=self.pr, role='reviewer')
        self.role.save()

        self.role = Role(team=self.t, person=self.pc, role='committer')
        self.role.save()

        self.role = Role(team=self.t, person=self.pcoo, role='coordinator')
        self.role.save()

        self.l = Language(name='french', locale='fr', team=self.t)
        self.l.save()

        self.m = Module(name='gedit', description='GNOME Editor',
            bugs_base="http://bugzilla.gnome.org/",
            bugs_product='gedit', bugs_component='general',
            vcs_type='svn', vcs_root="http://svn.gnome.org/svn",
            vcs_web="http://svn.gnome.org/viewvc/gedit")
        self.m.save()

        Branch.checkout_on_creation = False
        self.b = Branch(name='gnome-2-24', module=self.m) 
        # Block the update of Statistics by the thread
        self.b.save(update_statistics=False)

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
        for role in Role.objects.all():
            role.delete()
        self.t.delete()
        self.pn.delete()
        self.pt.delete()
        self.pr.delete()
        self.pc.delete()
        self.pcoo.delete()

    def test_state_none(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l)
        sdb.name = 'None'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateNone))

        action_names = [a.name for a in state.get_available_actions(self.pn)]
        self.assertEqual(action_names, ['WC'])

        for p in (self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC', None, 'IC'])
        
    def test_state_translating(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pt)
        sdb.name = 'Translating'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateTranslating))

        for p in (self.pn, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])
        
        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC', None, 'IC', 'BA'])

        # Same person
        action_names = [a.name for a in state.get_available_actions(self.pt)]
        self.assertEqual(action_names, ['UT', 'UNDO', 'WC'])

    def test_state_translated(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pt)
        sdb.name = 'Translated'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateTranslated))
        
        action_names = [a.name for a in state.get_available_actions(self.pn)]
        self.assertEqual(action_names, ['WC'])

        action_names = [a.name for a in state.get_available_actions(self.pt)]
        self.assertEqual(action_names, ['RT', 'TR', 'WC'])

        action_names = [a.name for a in state.get_available_actions(self.pr)]
        self.assertEqual(action_names, ['RP', 'RT', 'TR', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RP', 'RT', 'TR', 'WC', None, 'IC', 'BA'])

    def test_state_proofreading(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        sdb.name = 'Proofreading'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateProofreading))
        
        for p in (self.pn, self.pt):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC', None, 'IC', 'BA'])

        # Same person and reviewer
        action_names = [a.name for a in state.get_available_actions(self.pr)]
        self.assertEqual(action_names, ['UP', 'TR', 'TC', 'UNDO', 'WC'])
        
    def test_state_proofread(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        sdb.name = 'Proofread'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateProofread))

        for p in (self.pn, self.pt):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        action_names = [a.name for a in state.get_available_actions(self.pr)]
        self.assertEqual(action_names, ['TC', 'RP', 'TR', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['TC', 'RP', 'TR', 'WC', None, 'IC', 'BA'])

    def test_state_to_review(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pt)
        sdb.name = 'ToReview'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateToReview))

        action_names = [a.name for a in state.get_available_actions(self.pn)]
        self.assertEqual(action_names, ['WC'])

        for p in (self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC', None, 'IC', 'BA'])

    def test_state_to_commit(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        sdb.name = 'ToCommit'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateToCommit))

        for p in (self.pn, self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RC', 'TR', 'WC', None, 'IC', 'BA'])

    def test_state_committing(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pc)
        sdb.name = 'Committing'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateCommitting))

        for p in (self.pn, self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        action_names = [a.name for a in state.get_available_actions(self.pcoo)]
        self.assertEqual(action_names, ['WC', None, 'IC', 'BA'])

        action_names = [a.name for a in state.get_available_actions(self.pc)]
        self.assertEqual(action_names, ['IC', 'TR', 'UNDO', 'WC'])

    def test_state_committed(self):
        sdb = StateDb(branch=self.b, domain=self.d, language=self.l, person=self.pc)
        sdb.name = 'Committed'
        state = sdb.get_state()
        self.assert_(isinstance(state, StateCommitted))

        for p in (self.pn, self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['BA', 'WC', None, 'IC'])

    def test_action_wc(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='None').get_state()
        state.save()

        action = ActionAbstract.new_by_name('WC')
        new_state = state.apply_action(action, self.pt, "Hi!", None)
        new_state.save()

    def test_action_rt(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='None').get_state()
        state.save()

        action = ActionAbstract.new_by_name('RT')
        new_state = state.apply_action(action, self.pt, "Reserved!", None)
        new_state.save()

    def test_action_ut(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='Translating', person=self.pt).get_state()
        state.save()

        test_file = ContentFile('test content')
        test_file._name = 'mytestfile.po'

        action = ActionAbstract.new_by_name('UT')
        new_state = state.apply_action(action, self.pt, "Done by translator.", test_file)
        new_state.save()

    def test_action_rp(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='Translated').get_state()
        state.save()

        action = ActionAbstract.new_by_name('RP')
        new_state = state.apply_action(action, self.pr, "Reserved by a reviewer!")
        new_state.save()

    def test_action_up(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='Proofreading', person=self.pr).get_state()
        state.save()

        test_file = ContentFile('test content')
        test_file._name = 'mytestfile.po'

        action = ActionAbstract.new_by_name('UP')
        new_state = state.apply_action(action, self.pr, "Done.", test_file)
        new_state.save()

    def test_action_tc(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='Proofread').get_state()
        state.save()

        action = ActionAbstract.new_by_name('TC')
        new_state = state.apply_action(action, self.pr, "Ready!")
        new_state.save()

    def test_action_rc(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='ToCommit').get_state()
        state.save()

        action = ActionAbstract.new_by_name('RC')
        new_state = state.apply_action(action, self.pc, "This work is mine!")
        new_state.save()

    def test_action_ic(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='Proofreading', person=self.pr).get_state()
        state.save()

        # Create a new file
        test_file = ContentFile('test content')
        test_file._name = 'mytestfile.po'

        action = ActionAbstract.new_by_name('UP')
        state = state.apply_action(action, self.pr, "Done.", test_file)
        state.save()

        file_path = os.path.join(settings.MEDIA_ROOT, action.file.name)
        self.assert_(os.access(file_path, os.W_OK))

        action = ActionAbstract.new_by_name('TC')
        state = state.apply_action(action, self.pc, "To commit.")
        state.save()

        action = ActionAbstract.new_by_name('RC')
        state = state.apply_action(action, self.pc, "Reserved commit.")
        state.save()

        action = ActionAbstract.new_by_name('IC')
        state = state.apply_action(action, self.pc, "Committed.")
        state.save()

        self.assert_(not os.access(file_path, os.F_OK))
        
        # Remove test file
        backup_action = ActionDbBackup.objects.get(comment="Done.")
        backup_file_path = os.path.join(settings.MEDIA_ROOT, backup_action.file.name)
        backup_action.delete()
        self.assert_(not os.access(backup_file_path, os.F_OK))

    def test_action_tr(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='Translated').get_state()
        state.save()

        action = ActionAbstract.new_by_name('TR')
        new_state = state.apply_action(action, self.pc, "Bad work :-/")
        new_state.save()

    def test_action_ba(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='Committed', person=self.pr).get_state()
        state.save()

        action = ActionAbstract.new_by_name('BA')
        state = state.apply_action(action, self.pc, comment="I don't want to disappear")
        state.save()

    def test_action_undo(self):
        state = StateDb(branch=self.b, domain=self.d, language=self.l, name='None').get_state()
        state.save()

        action = ActionAbstract.new_by_name('RT')
        state = state.apply_action(action, self.pt, "Reserved!")
        state.save()

        action = ActionAbstract.new_by_name('UNDO')
        state = state.apply_action(action, self.pt, "Ooops! I don't want to do that. Sorry.")
        state.save()

        self.assertEqual(state.name, 'None')
        
        action = ActionAbstract.new_by_name('RT')
        state = state.apply_action(action, self.pt, "Translating")
        state.save()
        
        action = ActionAbstract.new_by_name('UT')
        state = state.apply_action(action, self.pt, "Translated")
        state.save()

        action = ActionAbstract.new_by_name('RT')
        state = state.apply_action(action, self.pt, "Reserved!")
        state.save()

        action = ActionAbstract.new_by_name('UNDO')
        state = state.apply_action(action, self.pt, "Ooops! I don't want to do that. Sorry.")
        state.save()

        self.assertEqual(state.name, 'Translated')
            
        action = ActionAbstract.new_by_name('RT')
        state = state.apply_action(action, self.pt, "Translating 1")
        state.save()
        
        action = ActionAbstract.new_by_name('UNDO')
        state = state.apply_action(action, self.pt, "Undo 1")
        state.save()
        
        action = ActionAbstract.new_by_name('RT')
        state = state.apply_action(action, self.pt, "Translating 2")
        state.save()
        
        action = ActionAbstract.new_by_name('UNDO')
        state = state.apply_action(action, self.pt, "Undo 2")
        state.save()
        
        self.assertEqual(state.name, 'Translated')
        
    def test_uploaded_file_validation(self):
        # Test a non valid po file
        post_content = QueryDict('action=WC&comment=Test1')
        post_file = MultiValueDict({'file': [SimpleUploadedFile('filename.po', 'Not valid po file content')]})
        form = ActionForm([('WC', u'Write a comment')], post_content, post_file)
        
        self.assert_('file' in form.errors)

        # Test a valid po file
        f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "valid_po.po"), 'r')
        post_file = MultiValueDict({'file': [File(f)]})
        form = ActionForm([('WC', u'Write a comment')], post_content, post_file)

        self.assert_(form.is_valid())
        
        # Test form without file
        form = ActionForm([('WC', u'Write a comment')], post_content)
        self.assert_(form.is_valid())

