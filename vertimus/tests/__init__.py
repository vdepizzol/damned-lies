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
from stats.tests import test_scratchdir
from vertimus.models import *
from vertimus.forms import ActionForm

class VertimusTest(TeamsAndRolesTests):

    def setUp(self):
        super(VertimusTest, self).setUp()

        self.m = Module.objects.create(name='gedit', description='GNOME Editor',
            bugs_base="http://bugzilla.gnome.org/",
            bugs_product='gedit', bugs_component='general',
            vcs_type='svn', vcs_root="http://svn.gnome.org/svn",
            vcs_web="http://svn.gnome.org/viewvc/gedit")

        Branch.checkout_on_creation = False
        self.b = Branch(name='gnome-2-24', module=self.m)
        # Block the update of Statistics by the thread
        self.b.save(update_statistics=False)

        self.r = Release.objects.create(name='gnome-2-24', status='official',
            description='GNOME 2.24 (stable)',
            string_frozen=True)

        self.c = Category.objects.create(release=self.r, branch=self.b, name='desktop')

        self.d = Domain.objects.create(module=self.m, name='po',
            description='UI translations',
            dtype='ui', directory='po')
        pot_stat = Statistics.objects.create(language=None, branch=self.b, domain=self.d)
        self.files_to_clean = []

    def tearDown(self):
        for path in self.files_to_clean:
            os.remove(path)

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
        self.assertEqual(action_names, ['RT', 'WC'])

        action_names = [a.name for a in state.get_available_actions(self.pr)]
        self.assertEqual(action_names, ['RP', 'TR', 'RT', 'WC'])

        for p in (self.pc, self.pcoo):
            action_names = [a.name for a in state.get_available_actions(p)]
            self.assertEqual(action_names, ['RP', 'TR', 'RT', 'TC', 'WC', None, 'IC', 'AA'])

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

        action = Action.new_by_name('WC', person=self.pt, comment="Hi!")
        action.apply_on(state)
        # Test that submitting a comment without text generates a validation error
        form = ActionForm([('WC', u'Write a comment')], QueryDict('action=WC&comment='))
        self.assertTrue("A comment is needed" in str(form.errors))

    def test_action_rt(self):
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('RT', person=self.pt, comment="Reserved!")
        action.apply_on(state)
        self.assertTrue(isinstance(state, StateTranslating))

    @test_scratchdir
    def test_action_ut(self):
        # Disabling the role
        role = Role.objects.get(person=self.pt, team=self.l.team)
        role.is_active = False
        role.save()
        
        state = StateTranslating(branch=self.b, domain=self.d, language=self.l, person=self.pt)
        state.save()

        test_file = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "valid_po.po"), 'r')

        action = Action.new_by_name('UT', person=self.pt, comment="Done by translator.", file=File(test_file))
        action.apply_on(state)
        self.assertEqual(action.file.url, '/media/upload/gedit-gnome-2-24-po-fr-%d.po' % state.id)
        self.assertEqual(action.merged_file.url(), '/media/upload/gedit-gnome-2-24-po-fr-%d.merged.po' % state.id)
        self.files_to_clean.extend([action.file.path, action.merged_file.path])

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

        action = Action.new_by_name('RP', person=self.pr, comment="Reserved by a reviewer!")
        action.apply_on(state)
        self.assertTrue(isinstance(state, StateProofreading))

    def test_action_up(self):
        state = StateProofreading(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        state.save()

        test_file = ContentFile('test content')
        test_file.name = 'mytestfile.po'

        action = Action.new_by_name('UP', person=self.pr, comment="Done.", file=test_file)
        action.apply_on(state)
        self.files_to_clean.append(action.file.path)
        self.assertTrue(isinstance(state, StateProofread))

    def test_action_tc(self):
        state = StateProofread(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('TC', person=self.pr, comment="Ready!")
        action.apply_on(state)
        self.assertTrue(isinstance(state, StateToCommit))

    def test_action_rc(self):
        state = StateToCommit(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('RC', person=self.pc, comment="This work is mine!")
        action.apply_on(state)
        self.assertTrue(isinstance(state, StateCommitting))

    def test_action_ic(self):
        state = StateProofreading(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        state.save()

        # Create a new file
        test_file = ContentFile('test content')
        test_file.name = 'mytestfile.po'

        action = Action.new_by_name('UP', person=self.pr, comment="Done.", file=test_file)
        action.apply_on(state)
        self.assertEquals(len(mail.outbox), 1) # Mail sent to mailing list
        mail.outbox = []

        file_path = os.path.join(settings.MEDIA_ROOT, action.file.name)
        self.assertTrue(os.access(file_path, os.W_OK))

        action = Action.new_by_name('TC', person=self.pc, comment="To commit.")
        action.apply_on(state)
        self.assertEquals(len(mail.outbox), 1) # Mail sent to committers
        mail.outbox = []

        action = Action.new_by_name('RC', person=self.pc, comment="Reserved commit.")
        action.apply_on(state)

        action = Action.new_by_name('IC', person=self.pc, comment="Committed.")
        action.apply_on(state)
        # Mail sent to mailing list
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].recipients(), [self.l.team.mailing_list])
        self.assertTrue(u'Commité' in mail.outbox[0].body) # Team is French

        self.assertTrue(isinstance(state, StateNone))
        self.assertTrue(not os.access(file_path, os.F_OK), "%s not deleted" % file_path)

        # Remove test file
        action_archived = ActionArchived.objects.get(comment="Done.")
        filename_archived = os.path.join(settings.MEDIA_ROOT, action_archived.file.name)
        action_archived.delete()
        self.assertTrue(not os.access(filename_archived, os.F_OK), "%s not deleted" % filename_archived)

    def test_action_tr(self):
        state = StateTranslated(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('TR', person=self.pc, comment="Bad work :-/")
        action.apply_on(state)
        self.assertTrue(isinstance(state, StateToReview))

    def test_action_aa(self):
        state = StateCommitted(branch=self.b, domain=self.d, language=self.l, person=self.pr)
        state.save()

        action = Action.new_by_name('AA', person=self.pc, comment="I don't want to disappear :)")
        action.apply_on(state)

        state = State.objects.get(branch=self.b, domain=self.d, language=self.l)
        self.assertTrue(isinstance(state, StateNone))
        self.assertEquals(state.action_set.count(), 0)

    def test_action_undo(self):
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('RT', person=self.pt, comment="Reserved!")
        action.apply_on(state)

        action = Action.new_by_name('UNDO', person=self.pt, comment="Ooops! I don't want to do that. Sorry.")
        action.apply_on(state)

        self.assertEqual(state.name, 'None')

        action = Action.new_by_name('RT', person=self.pt, comment="Translating")
        action.apply_on(state)

        action = Action.new_by_name('UT', person=self.pt, comment="Translated")
        action.apply_on(state)

        action = Action.new_by_name('RT', person=self.pt, comment="Reserved!")
        action.apply_on(state)

        action = Action.new_by_name('UNDO', person=self.pt, comment="Ooops! I don't want to do that. Sorry.")
        action.apply_on(state)

        self.assertEqual(state.name, 'Translated')

        action = Action.new_by_name('RT', person=self.pt, comment="Translating 1")
        action.apply_on(state)

        action = Action.new_by_name('UNDO', person=self.pt, comment="Undo 1")
        action.apply_on(state)

        action = Action.new_by_name('RT', person=self.pt, comment="Translating 2")
        action.apply_on(state)

        action = Action.new_by_name('UNDO', person=self.pt, comment="Undo 2")
        action.apply_on(state)

        self.assertEqual(state.name, 'Translated')

    def test_delete(self):
        """ Test that a whole module tree can be properly deleted """
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('WC', person=self.pt, comment="Hi!")
        action.apply_on(state)

        self.m.delete()
        self.assertEqual(Action.objects.all().count(), 0)

    def test_vertimus_view(self):
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

    def test_feeds(self):
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('RT', person=self.pt, comment="Translating")
        action.apply_on(state)

        response = self.client.get(reverse('lang_feed', args=[self.l.locale]))
        self.assertContains(response,
            """<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">""")
        self.assertContains(response,
            """<title>po (gedit/User Interface) - gedit (gnome-2-24) - Reserve for translation\n</title>""")
        self.assertContains(response,
            """<guid>http://example.com/vertimus/gedit/gnome-2-24/po/fr#%d</guid>""" % action.id)

        response = self.client.get(reverse('team_feed', args=[self.l.team.name]))
        self.assertContains(response,
            """<title>po (gedit/User Interface) - gedit (gnome-2-24) - Reserve for translation\n</title>""")

    def test_mysql(self):
        # Copied from test_action_undo() with minor changes
        state = StateNone(branch=self.b, domain=self.d, language=self.l)
        state.save()

        action = Action.new_by_name('RT', person=self.pr, comment="Reserved!")
        action.apply_on(state)

        action = Action.new_by_name('UNDO', person=self.pr, comment="Ooops! I don't want to do that. Sorry.")
        action.apply_on(state)

        action = Action.new_by_name('RT', person=self.pr, comment="Translating")
        action.apply_on(state)

        action = Action.new_by_name('UT', person=self.pr, comment="Translated")
        action.apply_on(state)

        action = Action.new_by_name('RP', person=self.pr, comment="Proofreading")
        action.apply_on(state)

        action = Action.new_by_name('UNDO', person=self.pr, comment="Ooops! I don't want to do that. Sorry.")
        action.apply_on(state)

        actions_db = Action.objects.filter(state_db__id=state.id).exclude(name='WC').order_by('-id')

        # So the last action is UNDO
        self.assert_(isinstance(actions_db[0], ActionUNDO))

        # Here be dragons! A call to len() workaround the Django/MySQL bug!
        len(actions_db)
        self.assert_(isinstance(actions_db[0], ActionUNDO))
