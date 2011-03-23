# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Claude Paroz <claude@2xlibre.net>
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

from django.core.urlresolvers import reverse
from django.test import TestCase

class LanguageTestCase(TestCase):
    fixtures = ['sample_data.json']

    def testLanguageReleaseXML(self):
        response = self.client.get(reverse("languages.views.language_release_xml", args=['fr', 'gnome-2-30']))
        self.assertContains(response, """<stats language="fr" release="gnome-2-30">""")
