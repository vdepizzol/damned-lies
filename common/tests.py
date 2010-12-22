# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Adorilson Bezerra <adorilson@gmail.com>
# Copyright (c) 2010 Claude Paroz <claude@2xlibre.net>
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

from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase

from common import views
from people.models import Person
from teams.models import Team, Role

class CommonTest(TestCase):

    def setUp(self):
        self.pn = Person(first_name='John', last_name='Note',
            email='jn@devnull.com', username= 'jn', activation_key='a_activation_key')
        self.pn.save()

        self.pr = Person(first_name='John', last_name='Reviewer',
            username='jr', date_joined=datetime.now()-timedelta(days=11),
            activation_key='non-activated-key') # non-activeted person
        self.pr.save()

        self.pt = Person(first_name='John', last_name='Translator',
            username='jt', last_login=datetime.now()-timedelta(days=30*6+1),) # inactive person
        self.pt.save()

        self.t1 = Team(name='fr', description='French')
        self.t1.save()
   
        self.t2 = Team(name='fr2', description='French')
        self.t2.save()

        self.r1 = Role(team=self.t1, person=self.pt)
        self.r1.save()

        self.r2 = Role(team=self.t2, person=self.pt)
        self.r2.save() 
        

    def test_activate_account(self):
        # Testing if is_active is False by default
        response = self.client.post(reverse('register'),
            {'username':'newuser', 'email': 'newuser@example.org',
             'password1': 'blah012', 'password2': 'blah012'})

        self.newu = Person.objects.get(username='newuser')
        self.assertFalse(self.newu.is_active)
        
        # Testing with a invalid activation key
        response = self.client.get('/register/activate/a_invalid_key')
        self.assertContains(response, 'Sorry, the key you provided is not valid.')        

        response = self.client.get('/register/activate/%s' % self.newu.activation_key)
        self.assertContains(response,  'Your account has been activated.')
        
        self.newu = Person.objects.get(username='newuser')
        self.assertTrue(self.newu.is_active)

    def test_house_keeping(self):
        response = self.client.get('/register/activate/a_activation_key')
        self.assertContains(response,  'Your account has been activated.')

        from django.core import management
        management.call_command('run-maintenance')

        # Testing if the non-activated accounts were deleted
        jn = Person.objects.filter(first_name='John', last_name='Note')
        self.assertEqual(jn.count(), 1)       

        jr = Person.objects.filter(first_name='John', last_name='Reviewer')
        self.assertEqual(jr.count(), 0)

        # Testing if the inactive roles were updated
        jt = Person.objects.get(first_name='John', last_name='Translator')
        for role in Role.objects.filter(person=jt):
            self.assertFalse(role.is_active)

