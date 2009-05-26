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

from django.conf import settings
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core import urlresolvers

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
            po_url = stats.po_url()
        except Statistics.DoesNotExist:
            # Get the POT file stats
            stats = get_object_or_404(Statistics, branch=branch, domain=domain, language=None)
            po_url = urlresolvers.reverse('dynamic_po',
                        args=("%s.%s.%s.%s.po" % (branch.module.name, domain.name, branch.name, language.locale),))
    else:
        po_url = stats.po_url()

    # Get the state of the translation
    (state_db, created) = StateDb.objects.get_or_create(
        branch=branch,
        domain=domain,
        language=language)
    other_branch_states = StateDb.objects.filter(domain=domain, language=language).exclude(branch=branch.pk).exclude(name='None')

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
        'po_url': po_url,
        'branch': branch,
        'other_states': other_branch_states,
        'domain': domain,
        'language': language,
        'module': branch.module,
        'non_standard_repo_msg' : _(settings.VCS_HOME_WARNING),
        'state': state,
        'action_history': action_history,
        'action_form': action_form
    }
    return render_to_response('vertimus/vertimus_detail.html', context,
                              context_instance=RequestContext(request))

def vertimus_diff(request, action_id_1, action_id_2=None):
    """Show a diff between current action po file and previous file"""
    import difflib
    action_1 = get_object_or_404(ActionDb, pk=action_id_1).get_action()
    state = action_1.state

    file_path_1 = action_1.merged_file()['path']
    if not file_path_1:
        # The merged file isn't availabe yet
        file_path_1 = action_1.file.path

    try:
        content_1 = [l.decode('utf-8') for l in open(file_path_1, 'U').readlines()]
    except UnicodeDecodeError:
        return render_to_response('error.html',
                                  {'error': _("Error: The file %s contains invalid characters.") % file_path_1.split('/')[-1]})
    descr_1 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action_1.person.name,
                                                             'date': action_1.created }
    if action_id_2 not in (None, "0"):
        # 1) id_2 specified in URL
        action_2 = get_object_or_404(ActionDb, pk=action_id_2).get_action()
        file_path_2 = action_2.merged_file()['path']
        descr_2 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action_2.person.name,
                                                                 'date': action_2.created }
    else:
        action_2 = None
        if action_id_2 is None:
            # 2) Search previous in action history
            action_2 = action_1.get_previous_action_with_po()

        if action_2:
            file_path_2 = action_2.merged_file()['path']
            descr_2 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action_2.person.name,
                                                                     'date': action_2.created }
        else:
             # 3) Lastly, the file should be the more recently committed file (merged)
            try:
                stats = Statistics.objects.get(branch=state.branch, domain=state.domain, language=state.language)
                descr_2 = _("Latest committed file for %(lang)s" % {'lang': state.language.get_name()})
            except Statistics.DoesNotExist:
                stats = get_object_or_404(Statistics, branch=state.branch, domain=state.domain, language=None)
                descr_2 = _("Latest POT file")
            file_path_2 = stats.po_path()
    try:
        content_2 = [l.decode('utf-8') for l in open(file_path_2, 'U').readlines()]
    except UnicodeDecodeError:
        return render_to_response('error.html',
                                  {'error': _("Error: The file %s contains invalid characters.") % file_path_2.split('/')[-1]})
    d = difflib.HtmlDiff(wrapcolumn=80)
    diff_content = d.make_table(content_2, content_1,
                                descr_2, descr_1, context=True)

    context = {
        'diff_content': diff_content,
        'state': state,
    }
    return render_to_response('vertimus/vertimus_diff.html', context,
                              context_instance=RequestContext(request))
