# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>
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

from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from stats.models import Statistics, Module, Branch, Domain, Language
from stats.utils import is_po_reduced
from vertimus.models import State, Action, ActionArchived
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

def vertimus_by_names(request, module_name, branch_name,
                      domain_name, locale_name, level="0"):
    """Access to Vertimus view by Branch, Domain and Language names"""
    module = get_object_or_404(Module, name=module_name)
    branch = get_object_or_404(Branch, name=branch_name, module__id=module.id)
    domain = get_object_or_404(Domain, name=domain_name, module__id=module.id)
    language = get_object_or_404(Language, locale=locale_name)
    return vertimus(request, branch, domain, language, level=level)

def vertimus(request, branch, domain, language, stats=None, level="0"):
    """The Vertimus view and form management. Level argument is used to
       access to the previous action history, first level (1) is the
       grandparent, second (2) is the parent of the grandparent, etc."""
    level = int(level)

    pot_stats = get_object_or_404(Statistics, branch=branch, domain=domain, language=None)
    if not stats:
        try:
            stats = Statistics.objects.get(branch=branch, domain=domain, language=language)
            po_url = stats.po_url()
        except Statistics.DoesNotExist:
            stats = pot_stats
            po_url = urlresolvers.reverse('dynamic_po',
                        args=("%s.%s.%s.%s.po" % (branch.module.name, domain.name, branch.name, language.locale),))
    else:
        po_url = stats.po_url()

    # Get the state of the translation
    (state, created) = State.objects.get_or_create(
        branch=branch,
        domain=domain,
        language=language)
    other_branch_states = State.objects.filter(
        domain=domain, language=language).exclude(branch=branch.pk).exclude(name='None')

    if level == 0:
        # Current actions
        action_history = Action.get_action_history(state=state)
    else:
        sequence = state.get_action_sequence_from_level(level)
        action_history = ActionArchived.get_action_history(sequence=sequence)

    # Get the sequence of the grandparent to know if exists a previous action
    # history
    sequence_grandparent = state.get_action_sequence_from_level(level + 1)
    grandparent_level = level + 1 if sequence_grandparent else None

    if request.user.is_authenticated() and level == 0:
        # Only authenticated user can act on the translation and it's not
        # possible to edit an archived workflow
        person = request.user.person

        available_actions = [(va.name, va.description)
                             for va in state.get_available_actions(person)]
        if request.method == 'POST':
            action_form = ActionForm(available_actions, request.POST, request.FILES)

            if action_form.is_valid():
                # Process the data in form.cleaned_data
                action = action_form.cleaned_data['action']
                comment = action_form.cleaned_data['comment']

                action = Action.new_by_name(action, person=person, comment=comment,
                    file=request.FILES.get('file', None))
                action.apply_on(state)

                return HttpResponseRedirect(
                    urlresolvers.reverse('vertimus_by_names',
                        args=(branch.module.name, branch.name, domain.name,
                              language.locale)))
        else:
            action_form = ActionForm(available_actions)
    else:
        action_form = None

    context = {
        'pageSection': 'module',
        'stats': stats,
        'pot_stats': pot_stats,
        'po_url': po_url,
        'po_url_reduced': stats.has_reducedstat() and stats.po_url(reduced=True) or '',
        'branch': branch,
        'other_states': other_branch_states,
        'domain': domain,
        'language': language,
        'module': branch.module,
        'non_standard_repo_msg' : _(settings.VCS_HOME_WARNING),
        'state': state,
        'action_history': action_history,
        'action_form': action_form,
        'level': level,
        'grandparent_level': grandparent_level,
    }
    return render(request, 'vertimus/vertimus_detail.html', context)


def vertimus_diff(request, action_id_1, action_id_2, level):
    """Show a diff between current action po file and previous file"""
    import difflib
    if int(level) != 0:
        ActionReal = ActionArchived
    else:
        ActionReal = Action
    action_1 = get_object_or_404(ActionReal, pk=action_id_1)
    state = action_1.state

    file_path_1 = action_1.merged_file()['path'] or action_1.file.path
    reduced = is_po_reduced(file_path_1)

    try:
        content_1 = [l.decode('utf-8') for l in open(file_path_1, 'U').readlines()]
    except UnicodeDecodeError:
        return render(request, 'error.html',
                      {'error': _("Error: The file %s contains invalid characters.") % file_path_1.split('/')[-1]})
    descr_1 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action_1.person.name,
                                                             'date': action_1.created }
    if action_id_2 not in (None, "0"):
        # 1) id_2 specified in URL
        action_2 = get_object_or_404(ActionReal, pk=action_id_2)
        file_path_2 = action_2.merged_file()['path'] or action_2.file.path
        descr_2 = _("Uploaded file by %(name)s on %(date)s") % { 'name': action_2.person.name,
                                                                 'date': action_2.created }
    else:
        action_2 = None
        if action_id_2 is None:
            # 2) Search previous in action history
            action_2 = action_1.get_previous_action_with_po()

        if action_2:
            file_path_2 = action_2.merged_file()['path'] or action_2.file.path
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
            file_path_2 = stats.po_path(reduced=reduced)
    try:
        content_2 = [l.decode('utf-8') for l in open(file_path_2, 'U').readlines()]
    except UnicodeDecodeError:
        return render(request, 'error.html',
                      {'error': _("Error: The file %s contains invalid characters.") % file_path_2.split('/')[-1]})
    d = difflib.HtmlDiff(wrapcolumn=80)
    diff_content = d.make_table(content_2, content_1,
                                descr_2, descr_1, context=True)

    context = {
        'diff_content': diff_content,
        'state': state,
    }
    return render(request, 'vertimus/vertimus_diff.html', context)

def latest_uploaded_po(request, module_name, branch_name, domain_name, locale_name):
    """ Redirect to the latest uploaded po for a module/branch/language """
    branch = get_object_or_404(Branch, module__name=module_name, name=branch_name)
    domain = get_object_or_404(Domain, module__name=module_name, name=domain_name)
    lang   = get_object_or_404(Language, locale=locale_name)
    latest_upload = Action.objects.filter(state_db__branch=branch,
                                          state_db__domain=domain,
                                          state_db__language=lang,
                                          file__endswith=".po").order_by('-created')[:1]
    if not latest_upload:
        raise Http404
    merged_file = latest_upload[0].merged_file()
    return HttpResponseRedirect(merged_file['url'])
