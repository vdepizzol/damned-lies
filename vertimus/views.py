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

from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core import urlresolvers
from django.conf import settings
from django.core.files.storage import default_storage

from people.models import Person
from stats.models import Statistics, Module, Branch, Domain, Language
from vertimus.models import StateDb, ActionDb, ActionAbstract

class ActionForm(forms.Form):
    action = forms.ChoiceField(label=_("Action"),
#        help_text="Choose an action you want to apply",
        choices=())
    comment = forms.CharField(label=_("Comment"),
#        help_text="Leave a comment to explain your action",
        max_length=1000,
        required=False,
        widget=forms.Textarea)
    file = forms.FileField(label=_("File"), required=False)

    def __init__(self, available_actions, *args, **kwargs):
        super(ActionForm, self).__init__(*args, **kwargs)
        self.fields['action'].choices = available_actions

def vertimus_by_stats_id(request, stats_id):
    """Access to Vertimus view by a Statistics ID"""
    stats = get_object_or_404(Statistics, pk=stats_id)
    return vertimus(request, stats.branch, stats.domain, stats.language, stats)

def vertimus_by_ids(request, branch_id, domain_id, language_id):
    """Access to Vertimus view by Branch, Domain and language IDs"""
    branch = get_object_or_404(Branch, pk=branch_id)
    domain = get_object_or_404(Domain, pk=domain_id)
    language = get_object_or_404(Language, pk=language_id)
    return vertimus(request, branch, domain, language)

def vertimus_by_names(request, module_name, branch_name, domain_name, locale_name):
    """Access to Vertimus view by Branch, Domain and language names"""
    module = get_object_or_404(Module, name=module_name)
    branch = get_object_or_404(Branch, name=branch_name, module__id=module.id)
    domain = get_object_or_404(Domain, name=domain_name, module__id=module.id)
    language = get_object_or_404(Language, locale=locale_name)

    return vertimus(request, branch, domain, language)

def handle_uploaded_file(f, branch, domain, language):
    filename = "%s-%s-%s-%s.po" % (branch.module.name, branch.name, domain.name, language.locale)
    path = default_storage.save(settings.UPLOAD_DIR + '/' + filename, f)
    
    # Keep only the new filename (duplicate files)
    return path

def vertimus(request, branch, domain, language, stats=None):
    """The Vertimus view and form management"""
    if not stats:
        stats = get_object_or_404(Statistics, branch=branch, domain=domain, language=language)

    # Get the state of the translation
    (state_db, created) = StateDb.objects.get_or_create(
        branch=branch,
        domain=domain,
        language=language)

    state = state_db.get_state()
    action_history = ActionDb.get_action_history(state_db)

    if request.user.is_authenticated():
        # Only authenticated user can act on the translation
        person = request.user.person
        
        available_actions = [(va.name, va.description) for va in state.get_available_actions(person)]
        if request.method == 'POST':
            action_form = ActionForm(available_actions, request.POST, request.FILES)

            if action_form.is_valid():
                # Process the data in form.cleaned_data
                action = action_form.cleaned_data['action']
                comment = action_form.cleaned_data['comment']
                
                if 'file' in request.FILES:
                    file = handle_uploaded_file(request.FILES['file'], branch, domain, language)
                else:
                    file = None

                action = ActionAbstract.new_by_name(action)
                new_state = state.apply_action(action, person, comment, file)
                new_state.save()

                return HttpResponseRedirect(
                    urlresolvers.reverse('vertimus-names-view', 
                        args=(branch.module.name, branch.name, domain.name, language.locale)))
        else:
            action_form = ActionForm(available_actions)
    else:
        action_form = None

    context = {
        'pageSection': 'module',
        'stats': stats,
        'branch': branch,
        'domain': domain,
        'language': language,
        'module': branch.module,
        'state': state,
        'action_history': action_history, 
        'action_form': action_form
    }
    return render_to_response('vertimus/vertimus_detail.html', context,
                              context_instance=RequestContext(request)) 
