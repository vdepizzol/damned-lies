# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Claude Paroz <claude@2xlibre.net>.
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>.
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

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from common import utils
from teams.models import Team, FakeTeam, Role
from teams.forms import EditMemberRoleForm
from languages.models import Language

def teams(request):
    teams = Team.objects.all_with_coordinator()

    context = {
        'pageSection': 'teams',
        'teams': utils.trans_sort_object_list(teams, 'description')
    }
    return render_to_response('teams/team_list.html', context, context_instance=RequestContext(request))

def team(request, team_slug):
    try:
        team = Team.objects.get(name=team_slug)
        coordinator = team.get_coordinator()
        mem_groups = (
               {'title': _("Committers"),
                'members': team.get_committers(),
                'form': None,
                'no_member': _("No committers")
               },
               {'title': _("Reviewers"),
                'members': team.get_reviewers(),
                'form': None,
                'no_member': _("No reviewers")
               },
               {'title': _("Translators"),
                'members': team.get_translators(),
                'form': None,
                'no_member': _("No translators")
               },
        )
    except Team.DoesNotExist:
        lang = get_object_or_404(Language, locale=team_slug)
        team = FakeTeam(lang)
        coordinator = None
        mem_groups = ()

    # Compare username because request.user is User and get_coordinator is Person
    if request.user.is_authenticated() and coordinator and request.user.username == coordinator.username:
        if request.method == 'POST':
            form_type = request.POST['form_type']
            roles = Role.objects.filter(team=team, role=form_type)
            form = EditMemberRoleForm(roles, request.POST)
            if form.is_valid():
                for key, field in form.fields.items():
                    form_value = form.cleaned_data[key]
                    if field.initial != form_value:
                        role = Role.objects.get(pk=key)
                        if form_value == "remove":
                            role.delete()
                        else:
                            role.role = form_value
                            role.save()
        # Create forms for template
        commit_roles = Role.objects.filter(team=team, role='committer')
        if commit_roles:
            mem_groups[0]['form'] = EditMemberRoleForm(commit_roles)
        review_roles = Role.objects.filter(team=team, role='reviewer')
        if review_roles:
            mem_groups[1]['form'] = EditMemberRoleForm(review_roles)
        translate_roles = Role.objects.filter(team=team, role='translator')
        if translate_roles:
            mem_groups[2]['form'] = EditMemberRoleForm(translate_roles)
    context = {
        'pageSection': 'teams',
        'team': team,
        'mem_groups': mem_groups
    }
    return render_to_response('teams/team_detail.html', context, context_instance=RequestContext(request))
