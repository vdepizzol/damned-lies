# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2011 Claude Paroz <claude@2xlibre.net>.
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
from datetime import date
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from common.utils import MIME_TYPES, get_user_locale
from stats.models import Statistics, FakeLangStatistics, Module, Branch, Category, Release
from stats.forms import ModuleBranchForm
from stats import utils
from languages.models import Language
from people.models import Person

def modules(request, format='html'):
    all_modules = Module.objects.all()
    if format in ('json', 'xml'):
        data = serializers.serialize(format, all_modules)
        return HttpResponse(data, mimetype=MIME_TYPES[format])
    context = {
        'pageSection':  "module",
        'modules': utils.sort_object_list(all_modules, 'get_description'),
    }
    return render(request, 'module_list.html', context)

def module(request, module_name):
    mod = get_object_or_404(Module, name=module_name)
    branches = mod.get_branches()
    if request.user.is_authenticated():
        person = Person.get_by_user(request.user)
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
        'user_language': get_user_locale(request)
    }
    return render(request, 'module_detail.html', context)

def module_branch(request, module_name, branch_name):
    """ This view is used to dynamically load a specific branch stats (jquery.load) """
    mod = get_object_or_404(Module, name=module_name)
    branch = mod.branch_set.get(name=branch_name)
    context = {
        'module': mod,
        'branch': branch,
    }
    return render(request, 'branch_detail.html', context)

@login_required
def module_edit_branches(request, module_name):
    mod = get_object_or_404(Module, name=module_name)
    if not mod.can_edit_branches(request.user):
        messages.error(request, "Sorry, you're not allowed to edit this module's branches")
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
                        messages.success(request, "The new branch %s has been added" % branch_name)
                        updated = True
                        # Send message to gnome-i18n?
                    except Exception, e:
                        messages.error(request, "Error adding the branch '%s': %s" % (branch_name, str(e)))
                        branch = None
                if branch and form.cleaned_data['new_branch_release']:
                    rel = Release.objects.get(pk=form.cleaned_data['new_branch_release'].pk)
                    cat = Category(release=rel, branch=branch, name=form.cleaned_data['new_branch_category'])
                    cat.save()
                    updated = True
            if updated:
                form = ModuleBranchForm(mod) # Redisplay a clean form
        else:
            messages.error(request, "Sorry, the form is not valid")
    else:
        form = ModuleBranchForm(mod)
    context = {
        'module': mod,
        'form': form,
    }
    return render(request, 'module_edit_branches.html', context)

def docimages(request, module_name, potbase, branch_name, langcode):
    mod = get_object_or_404(Module, name=module_name)
    try:
        stat = Statistics.objects.get(branch__module=mod.id,
                                      branch__name=branch_name,
                                      domain__name=potbase,
                                      language__locale=langcode)
    except Statistics.DoesNotExist:
        pot_stat = get_object_or_404(Statistics,
            branch__module=mod.id,
            branch__name=branch_name,
            domain__name=potbase,
            language__isnull=True)
        lang = get_object_or_404(Language, locale=langcode)
        stat = FakeLangStatistics(pot_stat, lang)
    context = {
        'pageSection': "module",
        'module':   mod,
        'stat':     stat,
        'locale':   stat.language.locale,
        'figstats': stat.fig_stats(),
    }
    return render(request, 'module_images.html', context)

def dynamic_po(request, module_name, domain, branch_name, filename):
    """ Generates a dynamic po file from the POT file of a branch """
    try:
        locale, ext = filename.split(".")
        if locale.endswith('-reduced'):
            locale, reduced = locale[:-8], True
        else:
            reduced = False
        language = Language.objects.select_related('team').get(locale=locale)
    except:
        raise Http404
    potfile = get_object_or_404(Statistics,
                             branch__module__name=module_name,
                             branch__name=branch_name,
                             domain__name=domain,
                             language=None)
    file_path = potfile.po_path(reduced=reduced).encode('ascii')
    if not os.access(file_path, os.R_OK):
        raise Http404

    dyn_content = u"""# %(lang)s translation for %(pack)s.
# Copyright (C) %(year)s %(pack)s's COPYRIGHT HOLDER
# This file is distributed under the same license as the %(pack)s package.\n""" % {
        'lang': language.name,
        'pack': module_name,
        'year': date.today().year
    }
    if request.user.is_authenticated():
        person = Person.get_by_user(request.user)
        dyn_content += u"# %(name)s <%(email)s>, %(year)s.\n#\n" % {
            'name' : person.name,
            'email': person.email,
            'year' : date.today().year,
        }
    else:
        dyn_content += u"# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.\n#\n"

    command = "msginit --locale=%s --no-translator --input=%s --output-file=-" % (locale, file_path)
    status, output, err = utils.run_shell_command(command, raise_on_error=True)
    lines = output.decode('utf-8').split("\n")
    skip_next_line = False
    for i, line in enumerate(lines):
        if skip_next_line or (line and line[0] == '#'):
            # Skip first lines of the file
            skip_next_line = False
            continue
        # Transformations
        new_line = {
            '"Project-Id-': u"\"Project-Id-Version: %s %s\\n\"" % (module_name, branch_name),
            '"Last-Transl': u"\"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n\"",
            '"Language-Te': u"\"Language-Team: %s <%s>\\n\"" % (
                language.name, language.team and language.team.mailing_list or "%s@li.org" % locale),
            '"Content-Typ': u"\"Content-Type: text/plain; charset=UTF-8\\n\"",
            '"Plural-Form': u"\"Plural-Forms: %s;\\n\"" % (language.plurals or "nplurals=INTEGER; plural=EXPRESSION"),
        }.get(line[:12], line)
        if line != new_line and line[-3:] != u"\\n\"":
            # Skip the wrapped part of the replaced line
            skip_next_line = True
        dyn_content += new_line + "\n"
        if line == "":
            # Output the remaining part of the file untouched
            dyn_content += "\n".join(lines[i+1:])
            break
    return HttpResponse(dyn_content, 'text/plain')

def releases(request, format='html'):
    active_releases = Release.objects.filter(weight__gte=0).order_by('status', '-weight', '-name')
    old_releases    = Release.objects.filter(weight__lt=0).order_by('status', '-weight', '-name')
    if format in ('json', 'xml'):
        from itertools import chain
        data = serializers.serialize(format, chain(active_releases, old_releases))
        return HttpResponse(data, mimetype=MIME_TYPES[format])
    context = {
        'pageSection'    : "releases",
        'active_releases': active_releases,
        'old_releases'   : old_releases,
    }
    return render(request, 'release_list.html', context)

def release(request, release_name, format='html'):
    release = get_object_or_404(Release, name=release_name)
    if format == 'xml':
        return render(request, 'release_detail.xml', { 'release' : release },
                                  content_type=MIME_TYPES[format])
    context = {
        'pageSection': "releases",
        'user_language': get_user_locale(request),
        'release': release
    }
    return render(request, 'release_detail.html', context)

def compare_by_releases(request, dtype, rels_to_compare):
    releases = []
    try:
        if "/" in rels_to_compare:
            # This is release names
            releases = [Release.objects.get(name='gnome-%s' % rel_name) for rel_name in rels_to_compare.split("/")]
        else:
            releases = [Release.objects.get(id=rel_id) for rel_id in rels_to_compare.split("-")]
    except Release.DoesNotExist:
        raise Http404
    stats = Release.total_by_releases(dtype, releases)
    context = {
        'releases': releases,
        'stats': stats
    }
    return render(request, 'release_compare.html', context)
