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
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from stats.models import Statistics, Module, Branch, Category, Release
from stats.forms import ModuleBranchForm
from stats.conf import settings
from stats import utils

MIME_TYPES = {'json': 'application/json',
              'xml':  'text/xml'
             }
def modules(request):
    all_modules = Module.objects.all()
    context = {
        'pageSection':  "module",
        'modules': utils.sort_object_list(all_modules, 'get_description')
    }
    return render_to_response('module_list.html', context, context_instance=RequestContext(request))

def module(request, module_name):
    mod = get_object_or_404(Module, name=module_name)
    context = {
        'pageSection':  "module",
        'module': mod,
        'can_edit_branches': mod.can_edit_branches(request.user),
        'prof': utils.Profiler()
    }
    return render_to_response('module_detail.html', context, context_instance=RequestContext(request))

@login_required
def module_edit_branches(request, module_name):
    mod = get_object_or_404(Module, name=module_name)
    messages = []
    if not mod.can_edit_branches(request.user):
        request.user.message_set.create(message="Sorry, you're not allowed to edit this module's branches")
        return module(request, module_name)
    if request.method == 'POST':
        form = ModuleBranchForm(mod, request.POST)
        if form.is_valid():
            updated = False
            # Modified or deleted release or category for branch
            for key, field in form.fields.items():
                if not getattr(field, 'is_branch', False):
                    continue
                if form.cleaned_data[key+'_del']:
                    # Delete category
                    Category.objects.get(pk=key).delete()
                    updated = True
                    continue
                release_has_changed = field.initial != form.cleaned_data[key].pk
                category_has_changed = form.fields[key+'_cat'].initial != form.cleaned_data[key+'_cat']
                if release_has_changed or category_has_changed:
                    old_release = Release.objects.get(pk=field.initial)
                    cat = Category.objects.get(pk=key)
                    if release_has_changed:
                        new_release = form.cleaned_data[key]
                        cat.release = new_release
                    cat.name = form.cleaned_data[key+'_cat']
                    cat.save()
                    updated = True
            # New branch (or new category)
            if form.cleaned_data['new_branch']:
                branch_name = form.cleaned_data['new_branch']
                try:
                    branch = Branch.objects.get(module=mod, name=branch_name)
                except Branch.DoesNotExist:
                    # It is probably a new branch
                    try:
                        branch = Branch(module=mod, name=branch_name)
                        branch.save()
                        messages.append("The new branch %s has been added" % branch_name)
                        updated = True
                        # Send message to gnome-i18n?
                    except Exception, e:
                        messages.append("Error adding the branch '%s': %s" % (branch_name, str(e)))
                        branch = None
                if branch and form.cleaned_data['new_branch_release']:
                    rel = Release.objects.get(pk=form.cleaned_data['new_branch_release'].pk)
                    cat = Category(release=rel, branch=branch, name=form.cleaned_data['new_branch_category'])
                    cat.save()
                    updated = True
            if updated:
                form = ModuleBranchForm(mod) # Redisplay a clean form
        else:
            messages.append("Sorry, form is not valid")
    else:  
        form = ModuleBranchForm(mod)
    context = {
        'module': mod,
        'form': form,
        'messages': messages
    }
    return render_to_response('module_edit_branches.html', context, context_instance=RequestContext(request))

def docimages(request, module_name, potbase, branch_name, langcode):
    mod = get_object_or_404(Module, name=module_name)
    stat = get_object_or_404(Statistics,
                             branch__module=mod.id, 
                             branch__name=branch_name,
                             domain__name=potbase,
                             language__locale=langcode)
    context = {
        'pageSection':  "module",
        'module': mod,
        'stat': stat
    }
    return render_to_response('module_images.html', context, context_instance=RequestContext(request))

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
        return render_to_response('release_list.html', context, context_instance=RequestContext(request))

def release(request, release_name):
    rel = get_object_or_404(Release, name=release_name)
    context = {
        'pageSection': "releases",
        'release': rel
    }
    return render_to_response('release_detail.html', context, context_instance=RequestContext(request))

