# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth import login
from people.models import Person
from teams.models import Team, Role

class TeamTest(TestCase):

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
            email='jc@alinsudesonpleingre.fr', username= 'jc')
        self.pc.save()

        self.pcoo = Person(first_name='John', last_name='Coordinator',
            email='jcoo@imthebigboss.fr', username= 'jcoo')
        self.pcoo.set_password('password')
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

    def tearDown(self):
        for role in Role.objects.all():
            role.delete()
        self.pcoo.delete()
        self.pc.delete()
        self.pr.delete()
        self.pt.delete()
        self.pn.delete()
        self.t.delete()

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

