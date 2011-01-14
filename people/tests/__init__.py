# -*- coding: utf-8 -*-
#
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

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.forms import ValidationError

from people.models import Person
from people import forms

class PeopleTestCase(TestCase):

    def test_register(self):
        response = self.client.post(reverse('register'),
                          {'username': u'test01', 'password1': u'1234567',
                           'password2': u'1234567', 'email': u'test01@example.org'})
        self.assertRedirects(response, reverse('register_success'))
        self.assertEqual(Person.objects.filter(username=u'test01').count(), 1)

    def test_edit_details(self):
        self.pn = Person(first_name='John', last_name='Nothing',
            email='jn@devnull.com', username= 'jn')
        self.pn.set_password('password')
        self.pn.save()
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
