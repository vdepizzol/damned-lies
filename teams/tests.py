from django.test import TestCase
from people.models import Person
from teams.models import Team, Role

class TeamTest(TestCase):

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

    def tearDown(self):
        for role in Role.objects.all():
            role.delete()
        self.pcoo.delete()
        self.pc.delete()
        self.pr.delete()
        self.pt.delete()
        self.pn.delete()
        self.t.delete()

    def test_roles(self):
        """
        Tests the hierarchy of roles
        """
        people = self.t.get_coordinator()
        self.assertEqual(people, self.pcoo)

        team = Team.objects.all_with_coordinator()[0]
        pcoo = team.get_coordinator()
        self.assertEqual(pcoo, self.pcoo)

        list_pc = team.get_committers()
        self.assertEqual(list_pc[0], self.pc)
