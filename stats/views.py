# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2009 Claude Paroz <claude@2xlibre.net>.
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
import codecs
from datetime import date

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from stats.models import Statistics, Module, Branch, Category, Release
from stats.forms import ModuleBranchForm
from stats import utils
from languages.models import Language

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
    branches = mod.get_branches()
    if request.user.is_authenticated():
        person = request.user.person
        langs = person.get_languages()
        for branch in branches:
            branch.get_ui_stats(mandatory_langs=langs)
            branch.get_doc_stats(mandatory_langs=langs)

    context = {
        'pageSection':  "module",
        'module': mod,
        'branches': branches,
        'non_standard_repo_msg' : _(settings.VCS_HOME_WARNING),
        'can_edit_branches': mod.can_edit_branches(request.user),
    }
    return render_to_response('module_detail.html', context, context_instance=RequestContext(request))

def module_branch(request, module_name, branch_name):
    """ This view is used to dynamically load a specific branch stats (jquery.load) """
    mod = get_object_or_404(Module, name=module_name)
    branch = mod.branch_set.get(name=branch_name)
    context = {
        'module': mod,
        'branch': branch,
    }
    return render_to_response('branch_detail.html', context, context_instance=RequestContext(request))

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
                if form.fields[key].initial and not form.cleaned_data[key]:
                    # Delete category
                    Category.objects.get(pk=key).delete()
                    updated = True
                    continue
                release_has_changed = field.initial != getattr(form.cleaned_data[key], 'pk', None)
                category_has_changed = form.fields[key+'_cat'].initial != form.cleaned_data[key+'_cat']
                if form.cleaned_data[key] and (release_has_changed or category_has_changed):
                    if field.initial:
                        old_release = Release.objects.get(pk=field.initial)
                        cat = Category.objects.get(pk=key)
                        if release_has_changed:
                            new_release = form.cleaned_data[key]
                            cat.release = new_release
                        cat.name = form.cleaned_data[key+'_cat']
                    else:
                        rel = Release.objects.get(pk=form.cleaned_data[key].pk)
                        branch = Branch.objects.get(module=mod, name=key)
                        cat = Category(release=rel, branch=branch, name=form.cleaned_data[key+'_cat'])
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

def dynamic_po(request, filename):
    """ Generates a dynamic po file from the POT file of a branch """
    try:
        module, domain, branch, locale, ext = filename.split(".")
        language = Language.objects.select_related('team').get(locale=locale)
    except:
        raise Http404
    potfile = get_object_or_404(Statistics,
                             branch__module__name=module,
                             branch__name=branch,
                             domain__name=domain,
                             language=None)
    file_path = potfile.po_path()
    f = codecs.open(file_path, encoding='utf-8')

    dyn_content = u"""# %(lang)s translation of %(pack)s.
# Copyright (C) %(year)s %(pack)s's COPYRIGHT HOLDER
# This file is distributed under the same license as the %(pack)s package.\n""" % {
        'lang': language.name,
        'pack': module,
        'year': date.today().year
    }
    if request.user.is_authenticated():
        person = request.user.person
        dyn_content += u"# %(name)s <%(email)s>, %(year)s.\n#\n" % {
            'name' : person.name,
            'email': person.email,
            'year' : date.today().year,
        }
    else:
        dyn_content += u"# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.\n#\n"

    line = "1"
    while line:
        line = f.readline()
        if line and line[0] == '#':
            # Skip first lines of the file
            continue
        # Transformations
        line = {
            '"Project-Id-': u"\"Project-Id-Version: %s %s\\n\"\n" % (module, branch),
            '"Language-Te': u"\"Language-Team: %s <%s>\\n\"\n" % (
                language.name, language.team and language.team.mailing_list or "%s@li.org" % locale),
            '"Content-Typ': u"\"Content-Type: text/plain; charset=UTF-8\\n\"\n",
            '"Plural-Form': u"\"Plural-Forms: %s;\\n\"\n" % (language.plurals or "nplurals=INTEGER; plural=EXPRESSION"),
        }.get(line[:12], line)
        dyn_content += line
        if line == "\n":
            break # Quit loop on first blank line after headers
    # codecs 'read' call doesn't always return all remaining buffer in first call. Bug?
    content = dyn_content + f.read() + f.read()
    return HttpResponse(content, 'text/plain')

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

def release(request, release_name, format='html'):
    release = get_object_or_404(Release, name=release_name)
    if format == 'xml':
        return render_to_response('release_detail.xml', { 'release' : release }, mimetype=MIME_TYPES[format])
    else:
        context = {
            'pageSection': "releases",
            'release': release
        }
        return render_to_response('release_detail.html', context, context_instance=RequestContext(request))

def compare_by_releases(request, dtype, rels_to_compare):
    releases = []
    for rel_id in rels_to_compare.split("-"):
        # Important to keep the ordering of the url
        releases.append(Release.objects.get(id=rel_id))
    stats = Release.total_by_releases(dtype, releases)
    context = {
        'releases': releases,
        'stats': stats
    }
    return render_to_response('release_compare.html', context, context_instance=RequestContext(request))
