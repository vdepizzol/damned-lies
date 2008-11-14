# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Claude Paroz <claude@2xlibre.net>.
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

from django.shortcuts import render_to_response, get_object_or_404
from stats.models import Statistics, Module, Release
from stats.conf import settings
from djamnedlies.stats import utils
from django.core import serializers
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

MIME_TYPES = {'json': 'application/json',
              'xml':  'text/xml'
             }
def modules(request):
    all_modules = Module.objects.all()
    context = {
        'pageSection':  "module",
        'modules': utils.sortObjectList(all_modules, 'description')
    }
    return render_to_response('module_list.html', context)

def module(request, module_name):
    mod = get_object_or_404(Module, name=module_name)
    context = {
        'pageSection':  "module",
        'module': mod,
        'prof': utils.Profiler()
    }
    return render_to_response('module.html', context)

def docimages(request, module_name, potbase, branch_name, langcode):
    mod = get_object_or_404(Module, name=module_name)
    stat = Statistics.objects.get(branch__module=mod.id, 
                                  branch__name=branch_name,
                                  domain__name=potbase,
                                  language__locale=langcode)
    context = {
        'pageSection':  "module",
        'module': mod,
        'stat': stat
    }
    return render_to_response('module_images.html', context)

def releases(request, format='html'):
    all_releases = Release.objects.order_by('status', '-name')
    if format in ('json', 'xml'):
        data = serializers.serialize(format, all_releases)
        return HttpResponse(data, mimetype=MIME_TYPES[format])
    else:
        context = {
            'pageSection':  "releases",
            'releases': all_releases
        }
        return render_to_response('release_list.html', context)

def release(request, release_name):
    rel = get_object_or_404(Release, name=release_name)
    context = {
        'pageSection': "releases",
        'release': rel
    }
    return render_to_response('release.html', context)

