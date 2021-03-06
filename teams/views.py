# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2011 Claude Paroz <claude@2xlibre.net>.
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _

from common import utils
from teams.models import Team, FakeTeam, Role
from teams.forms import EditMemberRoleForm, EditTeamDetailsForm
from languages.models import Language

def teams(request, format='html'):
    teams = Team.objects.all_with_coordinator()
    format = request.GET.get('format') or format
    if format == 'xml':
        return render(request, 'teams/team_list.xml', { 'teams' : teams },
            content_type=utils.MIME_TYPES[format]
        )
    else:
        context = {
            'pageSection': 'teams',
            'teams': utils.trans_sort_object_list(teams, 'description'),
        }
        return render(request, 'teams/team_list.html', context)

def team(request, team_slug):
    try:
        team = Team.objects.get(name=team_slug)
        coordinator = team.get_coordinator()
        mem_groups = (
               {'title': _("Committers"),
                'members': team.get_committers_exact(),
                'form': None,
                'no_member': _("No committers")
               },
               {'title': _("Reviewers"),
                'members': team.get_reviewers_exact(),
                'form': None,
                'no_member': _("No reviewers")
               },
               {'title': _("Translators"),
                'members': team.get_translators_exact(),
                'form': None,
                'no_member': _("No translators")
               },
               {'title': _("Inactive members"),
                'members': team.get_inactive_members(),
                'form': None,
                'no_member': _("No inactive members")
               },
        )
    except Team.DoesNotExist:
        lang = get_object_or_404(Language, locale=team_slug)
        team = FakeTeam(lang)
        coordinator = None
        mem_groups = ()

    context = {
        'pageSection': 'teams',
        'team': team,
        'can_edit_team': False,
    }
    if team.can_edit(request.user):
        if request.method == 'POST':
            form_type = request.POST['form_type']
            roles = Role.objects.filter(team=team, role=form_type, is_active=True)
            form = EditMemberRoleForm(roles, request.POST)
            if form.is_valid():
                for key, field in form.fields.items():
                    form_value = form.cleaned_data[key]
                    if field.initial != form_value:
                        role = Role.objects.get(pk=key)
                        if form_value == "remove":
                            role.delete()
                        elif form_value == "inactivate":
                            role.is_active = False
                            role.save()
                        else:
                            role.role = form_value
                            role.save()
        # Create forms for template
        commit_roles = Role.objects.filter(team=team, role='committer', is_active=True)
        if commit_roles:
            mem_groups[0]['form'] = EditMemberRoleForm(commit_roles)
        review_roles = Role.objects.filter(team=team, role='reviewer', is_active=True)
        if review_roles:
            mem_groups[1]['form'] = EditMemberRoleForm(review_roles)
        translate_roles = Role.objects.filter(team=team, role='translator', is_active=True)
        if translate_roles:
            mem_groups[2]['form'] = EditMemberRoleForm(translate_roles)
        context['can_edit_team'] = True

    context['mem_groups'] = mem_groups
    context['can_edit_details'] = context['can_edit_team'] or utils.is_site_admin(request.user)
    return render(request, 'teams/team_detail.html', context)

def team_edit(request, team_slug):
    team = get_object_or_404(Team, name=team_slug)
    if not (team.can_edit(request.user) or utils.is_site_admin(request.user)):
        return HttpResponseForbidden("You are not allowed to edit this team.")
    form = EditTeamDetailsForm(request.user, request.POST or None, instance=team)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('team_slug', args=[team_slug]))
    context = {
        'team': team,
        'form': form
    }
    return render(request, 'teams/team_edit.html', context)
