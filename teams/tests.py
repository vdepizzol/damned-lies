# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth import login
from people.models import Person
from teams.models import Team, Role
from languages.models import Language


class TeamsAndRolesTests(TestCase):
    def setUp(self):
        self.pn = Person(first_name='John', last_name='Nothing',
            email='jn@devnull.com', username= 'jn')
        self.pn.set_password('password')
        self.pn.save()

        self.pt = Person(first_name='John', last_name='Translator',
            email='jt@tf1.com', username= 'jt')
        self.pt.save()

        self.pr = Person(first_name='John', last_name='Reviewer',
            email='jr@csa.com', username= 'jr')
        self.pr.save()

        self.pc = Person(first_name='John', last_name='Committer',
            email='jc@alinsudesonpleingre.fr', username= 'jc',
            last_login=datetime.now()-timedelta(days=30*6-1)) #active person, but in limit date
        self.pc.save()

        self.pcoo = Person(first_name='John', last_name='Coordinator',
            email='jcoo@imthebigboss.fr', username= 'jcoo')
        self.pcoo.set_password('password')
        self.pcoo.save()

        self.t = Team(name='fr', description='French', mailing_list='french_ml@example.org')
        self.t.save()

        self.t2 = Team(name='pt', description='Portuguese')
        self.t2.save()

        self.l = Language(name='French', locale='fr', team=self.t)
        self.l.save()

        self.role = Role(team=self.t, person=self.pt)
        self.role.save()

        self.role = Role(team=self.t2, person=self.pt, role='reviewer')
        self.role.save()

        self.role = Role(team=self.t, person=self.pr, role='reviewer')
        self.role.save()

        self.role = Role(team=self.t, person=self.pc, role='committer')
        self.role.save()

        self.role = Role(team=self.t, person=self.pcoo, role='coordinator')
        self.role.save()

class TeamTest(TeamsAndRolesTests):
    def setUp(self):
        super(TeamTest, self).setUp()

    def test_get_members_by_role_exact(self):
        members = self.t.get_members_by_role_exact('committer')
        t = Team.objects.get(name='fr')
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0], self.pc)

        role = Role.objects.get(person=self.pc, team=t)
        role.is_active = False
        role.save()

        members = self.t.get_members_by_role_exact('committer')
        self.assertEqual(len(members), 0)

    def test_get_inactive_members(self):
        members = self.t.get_inactive_members()
        self.assertEqual(len(members), 0)

        t = Team.objects.get(name='fr')
        role = Role.objects.get(person=self.pc, team=t)
        role.is_active = False
        role.save()

        members = self.t.get_inactive_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0], self.pc)

    def run_roles_exact_test(self, team):
        pcoo = team.get_coordinator()
        self.assertEqual(pcoo, self.pcoo)

        members = team.get_committers_exact()
        self.assert_(len(members), 1)
        self.assertEqual(members[0], self.pc)

        members = team.get_reviewers_exact()
        self.assert_(len(members), 1)
        self.assertEqual(members[0], self.pr)

        members = team.get_translators_exact()
        self.assert_(len(members), 1)
        self.assertEqual(members[0], self.pt)

    def test_roles_exact(self):
        self.run_roles_exact_test(self.t)

    def test_roles_exact_prefilled_coordinator(self):
        self.run_roles_exact_test(Team.objects.all_with_coordinator()[0])

    def test_roles_exact_prefilled_all(self):
        self.run_roles_exact_test(Team.objects.all_with_roles()[0])

    def run_roles_test(self, team):
        """
        Tests the hierarchy of roles
        """
        members = team.get_committers()
        self.assertEqual(len(members), 2)
        for pc in members:
            self.assert_(pc in [self.pcoo, self.pc])

        members = team.get_reviewers()
        self.assertEqual(len(members), 3)
        for pc in members:
            self.assert_(pc in [self.pcoo, self.pc, self.pr])

        members = team.get_translators()
        self.assertEqual(len(members), 4)
        for pc in members:
            self.assert_(pc in [self.pcoo, self.pc, self.pr, self.pt])

    def test_roles(self):
        self.run_roles_test(self.t)

    def test_roles_prefilled_coordinator(self):
        self.run_roles_test(Team.objects.all_with_coordinator()[0])

    def test_roles_prefilled_all(self):
        self.run_roles_test(Team.objects.all_with_roles()[0])

    def test_join_team(self):
        c = Client()
        response = c.post('/login/', {'username': self.pn.username, 'password': 'password'})
        # Display team join page
        team_join_url = reverse('person_team_join', current_app='people')
        response = c.get(team_join_url)
        self.assertContains(response, "select name=\"teams\"")
        # Post for joining
        response = c.post(team_join_url, {'teams':[str(self.t.pk)]})
        # Test user is member of team
        self.assertTrue(self.pn.is_translator(self.t))
        # Test coordinator receives email
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].recipients()[0], self.pcoo.email)
        # Mail should be sent in the target team's language (i.e. French here)
        self.assertTrue(u"rejoindre" in mail.outbox[0].body)

    def test_edit_team(self):
        """ Test team edit form """
        c = Client()
        edit_url = reverse('team_edit', args = ['fr'], current_app='teams')
        response = c.get(edit_url)
        self.assertEquals(response.status_code, 403)
        # Login as team coordinator
        response = c.post('/login/', {'username': self.pcoo.username, 'password': 'password'})
        # Try team modification
        response = c.post(edit_url, {
            'webpage_url'  : u"http://www.gnomefr.org/",
            'mailing_list' : u"gnomefr@traduc.org",
            'mailing_list_subscribe': u""
        })
        team = Team.objects.get(name='fr')
        self.assertEquals(team.webpage_url, u"http://www.gnomefr.org/")


class RoleTest(TeamsAndRolesTests):

    def setUp(self):
        super(RoleTest, self).setUp()

        self.pt.last_login = datetime.now()-timedelta(days=10) # active person
        self.pt.save()

        self.pr.last_login = datetime.now()-timedelta(days=30*6) # inactive person
        self.pr.save()

        self.pc.last_login = datetime.now()-timedelta(days=30*6-1) #active person, but in limit date
        self.pc.save()

        self.role = Role.objects.get(team=self.t, person=self.pt)
        self.role2 = Role.objects.get(team=self.t2, person=self.pt)
        self.role_inactive = Role.objects.get(team=self.t, person=self.pr)
        self.role_limit_date = Role.objects.get(team=self.t, person=self.pc)

    def test_inactivating_roles(self):
        # Testing if is_active is True by default
        self.assertTrue(self.role.is_active)
        self.assertTrue(self.role2.is_active)
        self.assertTrue(self.role_limit_date.is_active)
        self.assertTrue(self.role_inactive.is_active)

        Role.inactivate_unused_roles()

        # Getting roles from database after update the unused roles
        self.role = Role.objects.get(team=self.t, person=self.pt)
        self.role2 = Role.objects.get(team=self.t2, person=self.pt)
        self.role_inactive = Role.objects.get(team=self.t, person=self.pr)
        self.role_limit_date = Role.objects.get(team=self.t, person=self.pc)

        self.assertTrue(self.role.is_active)
        self.assertTrue(self.role2.is_active)
        self.assertTrue(self.role_limit_date.is_active)
        self.assertFalse(self.role_inactive.is_active)
