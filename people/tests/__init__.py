# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011 Claude Paroz <claude@2xlibre.net>
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

import datetime

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.forms import ValidationError

from people.models import Person
from people import forms

class PeopleTestCase(TestCase):

    def _create_person(self, seq='', **kwargs):
        pn = Person(first_name='John', last_name='Nothing',
            email='jn%s@devnull.com' % seq, username= 'jn%s' % seq)
        for key, arg in kwargs.items():
            setattr(pn, key, arg)
        pn.set_password('password')
        pn.save()
        return pn

    def test_register(self):
        response = self.client.post(reverse('register'),
                          {'username': u'test01', 'password1': u'1234567',
                           'password2': u'1234567', 'email': u'test01@example.org'})
        self.assertRedirects(response, reverse('register_success'))
        self.assertEqual(Person.objects.filter(username=u'test01').count(), 1)

    def test_person_list(self):
        self.pn = self._create_person()
        response = self.client.get(reverse('people'))
        self.assertContains(response, "GNOME is being developed by following people:")
        self.assertContains(response, "John Nothing")

    def test_edit_details(self):
        self.pn = self._create_person()
        self.client.login(username='jn', password='password')
        post_data = {
            'first_name': "Johnny", 'last_name': "Nothing", 'email': u'test02@example.org',
            'image': '', 'webpage_url': "http://www.example.org/"
        }
        response = self.client.post(reverse('person_detail_change'), post_data)
        self.pn = Person.objects.get(pk=self.pn.pk)
        self.assertEqual(self.pn.email, u'test02@example.org')
        # bad image url
        post_data['image'] = "http://http://www.example.org/image.jpg"
        form = forms.DetailForm(post_data, instance=self.pn)
        self.assertFalse(form.is_valid())
        self.assertTrue('image' in form.errors)

    def test_obsolete_accounts(self):
        from teams.models import Team, Role
        from stats.models import Module, Branch, Domain
        from languages.models import Language
        from vertimus.models import StateTranslating
        module = Module.objects.create(name="gnome-hello")
        Branch.checkout_on_creation = False
        branch = Branch(name='gnome-2-24', module=module)
        branch.save(update_statistics=False)
        domain = Domain.objects.create(module=module, name='po', directory='po')
        team = Team.objects.create(name='fr', description='French', mailing_list='french_ml@example.org')
        lang = Language.objects.create(name='French', locale='fr', team=team)

        # Create Users
        p1 = self._create_person(seq='1', last_login=datetime.datetime.now()-datetime.timedelta(days=700))
        p2 = self._create_person(seq='2', last_login=datetime.datetime.now()-datetime.timedelta(days=800))
        role = Role.objects.create(team=team, person=p2, role='coordinator')
        p3 = self._create_person(seq='3', last_login=datetime.datetime.now()-datetime.timedelta(days=800))
        module.maintainers.add(p3)
        p4 = self._create_person(seq='4', last_login=datetime.datetime.now()-datetime.timedelta(days=800))
        state = StateTranslating.objects.create(branch=branch, domain=domain, language=lang, person=p4)
        p5 = self._create_person(seq='5', last_login=datetime.datetime.now()-datetime.timedelta(days=800))
        # Test only p5 should be deleted
        self.assertEqual(Person.objects.all().count(), 5)
        Person.clean_obsolete_accounts()
        import pdb; pdb.set_trace()
        self.assertEqual(Person.objects.all().count(), 4)
        self.assertEqual(set(Person.objects.all()), set([p1, p2, p3, p4]))
