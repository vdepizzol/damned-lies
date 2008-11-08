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

from django.shortcuts import render_to_response
from common import utils
from languages.models import Language
from stats.models import Release

def languages(request):
    languages = Language.objects.all()
    context = {
        'pageSection': "languages",
        'languages': utils.trans_sort_object_list(languages, 'name')
    }
    return render_to_response('languages/language_list.html', context)

def language_release(request, locale, release_name):
    language = Language.objects.get(locale=Language.unslug_locale(locale))
    release = Release.objects.get(name=release_name)
    stats = release.get_lang_stats(language)
    context = {
        'pageSection': "languages",
        'language': language,
        'release': release,
        'stats': stats
    }
    return render_to_response('languages/language_release.html', context)
