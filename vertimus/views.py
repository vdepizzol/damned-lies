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
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core import urlresolvers
from django.conf import settings

from people.models import Person
from stats.models import Statistics, Module, Branch, Domain, Language
from vertimus.models import StateDb, ActionDb, ActionAbstract
from vertimus.forms import ActionForm

def vertimus_by_stats_id(request, stats_id, lang_id):
    """Access to Vertimus view by a Statistics ID"""
    stats = get_object_or_404(Statistics, pk=stats_id)
    lang = get_object_or_404(Language, pk=lang_id)
    return vertimus(request, stats.branch, stats.domain, lang, stats)

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

def vertimus(request, branch, domain, language, stats=None):
    """The Vertimus view and form management"""
    if not stats:
        try:
            stats = Statistics.objects.get(branch=branch, domain=domain, language=language)
        except Statistics.DoesNotExist:
            # Get the POT file stats
            stats = get_object_or_404(Statistics, branch=branch, domain=domain, language=None)

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
                
                action = ActionAbstract.new_by_name(action)
                new_state = state.apply_action(action, person, comment, request.FILES.get('file', None))
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

def vertimus_diff(request, action_id, action_id2=None):
    """ Show a diff between current action po file and previous file """
    import difflib
    action_db1 = get_object_or_404(ActionDb, pk=action_id)
    state = action_db1.state_db
    file_path1 = action_db1.get_action().merged_file()['path']
    if not file_path1:
        file_path1 = action_db1.file.path
    content1 = [l.decode('utf-8') for l in open(file_path1, 'U').readlines()]
    descr1 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action_db1.person.name,
                                                            'date': action_db1.created }
    if action_id2 is None:
        # Search previous in action history
        action2 = action_db1.get_previous_action_with_po()
        if action2:
            file_path2 = action2.merged_file()['path']
            descr2 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action2.person.name,
                                                                    'date': action2.created }
    if action_id2 == "0" or (not action_id2 and not action2):
         # The file should be the more recently committed file (merged)
        try:
            stats = Statistics.objects.get(branch=state.branch, domain=state.domain, language=state.language)
            descr2 = _("Latest committed file for %(lang)s" % {'lang': state.language.get_name()})
        except Statistics.DoesNotExist:
            stats = get_object_or_404(Statistics, branch=state.branch, domain=state.domain, language=None)
            descr2 = _("Latest POT file")
        file_path2 = stats.po_path()
    else:
        # id2 specified in url
        action2 = ActionDb.objects.get(id=action_id2)
        file_path2 = action2.file.path
        descr2 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action2.person.name,
                                                                'date': action2.created }
    content2 = [l.decode('utf-8') for l in open(file_path2, 'U').readlines()]
    d = difflib.HtmlDiff()
    diff_content = d.make_table(content2, content1,
                                descr2, descr1, context=True)

    context = {
        'diff_content': diff_content,
        'state': state,
    }
    return render_to_response('vertimus/vertimus_diff.html', context,
                              context_instance=RequestContext(request))
