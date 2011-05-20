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

from django.conf import settings
from django.core.files.base import File, ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict

from teams.tests import TeamsAndRolesTests
from stats.models import Module, Branch, Release, Category, Domain, Statistics
from vertimus.models import *
from vertimus.forms import ActionForm

class VertimusTest(TeamsAndRolesTests):

    def setUp(self):
        super(VertimusTest, self).setUp()

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

    def test_state_none(self):
        state = StateNone(branch=self.b, domain=self.d, language=self.l)

        action_names = [a.name for a in state.get_available_actions(self.pn)]
        self.assertEqual(action_names, ['WC'])

        for p in (self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC', None, 'IC'])

    def test_state_translating(self):
        state = StateTranslating(branch=self.b, domain=self.d, language=self.l, person=self.pt)

        for p in (self.pn, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC', None, 'IC', 'AA'])

        # Same person
        action_names = [a.name for a in state.get_available_actions(self.pt)]
        self.assertEqual(action_names, ['UT', 'UNDO', 'WC'])

    def test_state_translated(self):
        state = StateTranslated(branch=self.b, domain=self.d, language=self.l, person=self.pt)

        action_names = [a.name for a in state.get_available_actions(self.pn)]
        self.assertEqual(action_names, ['WC'])

        action_names = [a.name for a in state.get_available_actions(self.pt)]
        self.assertEqual(action_names, ['RT', 'TR', 'WC'])

        action_names = [a.name for a in state.get_available_actions(self.pr)]
        self.assertEqual(action_names, ['RP', 'RT', 'TR', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RP', 'RT', 'TR', 'TC', 'WC', None, 'IC', 'AA'])

    def test_state_proofreading(self):
        state = StateProofreading(branch=self.b, domain=self.d, language=self.l, person=self.pr)

        for p in (self.pn, self.pt):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC', None, 'IC', 'AA'])

        # Same person and reviewer
        action_names = [a.name for a in state.get_available_actions(self.pr)]
        self.assertEqual(action_names, ['UP', 'TR', 'TC', 'UNDO', 'WC'])

    def test_state_proofread(self):
        state = StateProofread(branch=self.b, domain=self.d, language=self.l, person=self.pr)

        for p in (self.pn, self.pt):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        action_names = [a.name for a in state.get_available_actions(self.pr)]
        self.assertEqual(action_names, ['TC', 'RP', 'TR', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['TC', 'RP', 'TR', 'WC', None, 'IC', 'AA'])

    def test_state_to_review(self):
        state = StateToReview(branch=self.b, domain=self.d, language=self.l, person=self.pt)

        action_names = [a.name for a in state.get_available_actions(self.pn)]
        self.assertEqual(action_names, ['WC'])

        for p in (self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RT', 'WC', None, 'IC', 'AA'])

    def test_state_to_commit(self):
        state = StateToCommit(branch=self.b, domain=self.d, language=self.l, person=self.pr)

        for p in (self.pn, self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RC', 'TR', 'WC', None, 'IC', 'AA'])

    def test_state_committing(self):
        state = StateCommitting(branch=self.b, domain=self.d, language=self.l, person=self.pc)

        for p in (self.pn, self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        action_names = [a.name for a in state.get_available_actions(self.pcoo)]
        self.assertEqual(action_names, ['WC', None, 'IC', 'AA'])

        action_names = [a.name for a in state.get_available_actions(self.pc)]
        self.assertEqual(action_names, ['IC', 'TR', 'UNDO', 'WC'])

    def test_state_committed(self):
        state = StateCommitted(branch=self.b, domain=self.d, language=self.l, person=self.pc)

        for p in (self.pn, self.pt, self.pr):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['AA', 'WC', None, 'IC'])

    def test_action_wc(self):
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('WC')
        state.apply_action(action, self.pt, "Hi!", None)
        # Test that submitting a comment without text generates a validation error
        form = ActionForm([('WC', u'Write a comment')], QueryDict('action=WC&comment='))
        self.assertTrue("A comment is needed" in str(form.errors))

    def test_action_rt(self):
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pt, "Reserved!", None)
        self.assertTrue(isinstance(state, StateTranslating))

    def test_action_ut(self):
        # Disabling the role
        role = Role.objects.get(person=self.pt, team=self.l.team)
        role.is_active = False
        role.save()
        
        state = StateTranslating(branch=self.b, domain=self.d, language=self.l, person=self.pt)
        state.save()

        test_file = ContentFile('test content')
        test_file.name = 'mytestfile.po'
        
        action = ActionAbstract.new_by_name('UT')
        state.apply_action(action, self.pt, "Done by translator.", test_file)
        self.assertTrue(isinstance(state, StateTranslated))
        # Mail sent to mailing list
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].recipients(), [self.l.team.mailing_list])
        self.assertEquals(mail.outbox[0].subject, u"gedit - gnome-2-24")

        # Testing if the role was activated
        role = Role.objects.get(person=self.pt, team=self.l.team)
        self.assertTrue(role.is_active)

    def test_action_rp(self):
        state = StateTranslated(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('RP')
        state.apply_action(action, self.pr, "Reserved by a reviewer!")
        self.assertTrue(isinstance(state, StateProofreading))

    def test_action_up(self):
        state = StateProofreading(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        state.save()

        test_file = ContentFile('test content')
        test_file.name = 'mytestfile.po'

        action = ActionAbstract.new_by_name('UP')
        state.apply_action(action, self.pr, "Done.", test_file)
        self.assertTrue(isinstance(state, StateProofread))

    def test_action_tc(self):
        state = StateProofread(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('TC')
        state.apply_action(action, self.pr, "Ready!")
        self.assertTrue(isinstance(state, StateToCommit))

    def test_action_rc(self):
        state = StateToCommit(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('RC')
        state.apply_action(action, self.pc, "This work is mine!")
        self.assertTrue(isinstance(state, StateCommitting))

    def test_action_ic(self):
        state = StateProofreading(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        state.save()

        # Create a new file
        test_file = ContentFile('test content')
        test_file.name = 'mytestfile.po'

        action = ActionAbstract.new_by_name('UP')
        state.apply_action(action, self.pr, "Done.", test_file)

        file_path = os.path.join(settings.MEDIA_ROOT, action.file.name)
        self.assertTrue(os.access(file_path, os.W_OK))

        action = ActionAbstract.new_by_name('TC')
        state.apply_action(action, self.pc, "To commit.")

        action = ActionAbstract.new_by_name('RC')
        state.apply_action(action, self.pc, "Reserved commit.")

        action = ActionAbstract.new_by_name('IC')
        state.apply_action(action, self.pc, "Committed.")

        self.assertTrue(not os.access(file_path, os.F_OK), "%s not deleted" % file_path)

        # Remove test file
        action_db_archived = ActionDbArchived.objects.get(comment="Done.")
        filename_archived = os.path.join(settings.MEDIA_ROOT, action_db_archived.file.name)
        action_db_archived.delete()
        self.assertTrue(not os.access(filename_archived, os.F_OK), "%s not deleted" % filename_archived)

    def test_action_tr(self):
        state = StateTranslated(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('TR')
        state.apply_action(action, self.pc, "Bad work :-/")
        self.assertTrue(isinstance(state, StateToReview))

    def test_action_ba(self):
        state = StateCommitted(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        state.save()

        action = ActionAbstract.new_by_name('AA')
        state.apply_action(action, self.pc, comment="I don't want to disappear :)")

        state = State.objects.get(branch=self.b, domain=self.d, language=self.l)
        self.assertTrue(isinstance(state, StateNone))

    def test_action_undo(self):
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pt, "Reserved!")

        action = ActionAbstract.new_by_name('UNDO')
        state.apply_action(action, self.pt, "Ooops! I don't want to do that. Sorry.")

        self.assertEqual(state.name, 'None')

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pt, "Translating")

        action = ActionAbstract.new_by_name('UT')
        state.apply_action(action, self.pt, "Translated")

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pt, "Reserved!")

        action = ActionAbstract.new_by_name('UNDO')
        state.apply_action(action, self.pt, "Ooops! I don't want to do that. Sorry.")

        self.assertEqual(state.name, 'Translated')

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pt, "Translating 1")

        action = ActionAbstract.new_by_name('UNDO')
        state.apply_action(action, self.pt, "Undo 1")

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pt, "Translating 2")

        action = ActionAbstract.new_by_name('UNDO')
        state.apply_action(action, self.pt, "Undo 2")

        self.assertEqual(state.name, 'Translated')

    def test_vertimus_view(self):
        pot_stat = Statistics(language=None, branch=self.b, domain=self.d)
        pot_stat.save()

        url = reverse('vertimus_by_ids', args=[self.b.id, self.d.id, self.l.id])
        response = self.client.get(url)
        self.assertNotContains(response, '<option value="WC">')

        self.client.login(username=self.pn.username, password='password')
        response = self.client.get(url)
        self.assertContains(response, '<option value="WC">')

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

    def test_mysql(self):
        # Copied from test_action_undo() with minor changes
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pr, "Reserved!")

        action = ActionAbstract.new_by_name('UNDO')
        state.apply_action(action, self.pr, "Ooops! I don't want to do that. Sorry.")

        action = ActionAbstract.new_by_name('RT')
        state.apply_action(action, self.pr, "Translating")

        action = ActionAbstract.new_by_name('UT')
        state.apply_action(action, self.pr, "Translated")

        action = ActionAbstract.new_by_name('RP')
        state.apply_action(action, self.pr, "Proofreading")

        action = ActionAbstract.new_by_name('UNDO')
        state.apply_action(action, self.pr, "Ooops! I don't want to do that. Sorry.")

        actions_db = ActionDb.objects.filter(state_db__id=state.id).exclude(name='WC').order_by('-id')

        # So the last action is UNDO
        self.assert_(isinstance(actions_db[0].get_action(), ActionUNDO))

        # Here be dragons! A call to len() workaround the Django/MySQL bug!
        len(actions_db)
        self.assert_(isinstance(actions_db[0].get_action(), ActionUNDO))
