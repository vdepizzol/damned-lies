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
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.db import IntegrityError
from people.models import Person
from teams.models import Role
from people.forms import JoinTeamForm, EditProfileForm

def person_detail_from_username(request, slug, edit_profile=False):
    person = get_object_or_404(Person, username=slug)
    return person_detail(request, person, edit_profile)

def person_detail_from_id(request, object_id, edit_profile=False):
    person = get_object_or_404(Person, pk=object_id)
    return person_detail(request, person, edit_profile)

def person_detail(request, person, edit_profile):
    messages = []
    # Handle the form to join a team
    if request.method == 'POST' and request.POST.get('join_team_form',None):
        join_form = JoinTeamForm(request.POST)
        if join_form.is_valid():
            if request.user.username == person.username:
                team = join_form.cleaned_data['teams']
                new_role = Role(team=team, person=person) # role default to translator
                try:
                    new_role.save()
                except IntegrityError:
                    messages.append(_("You are already member of this team."))
            else:
                messages.append(_("Sorry, you're not allowed to modify this user."))
    else:
        join_form = JoinTeamForm()
    # Handle the form to edit profile
    profile_form = None
    if request.method == 'POST' and request.POST.get('edit_profile_form',None):
        form = EditProfileForm(request.POST, instance=person)
        if form.is_valid():
            if request.user.username == person.username:
                form.save()
            else:
                messages.append(_("Sorry, you're not allowed to modify this user."))
        else:
            messages.append("Sorry, the form is not valid.")
            profile_form = form
    elif edit_profile:
        profile_form = EditProfileForm(instance=person)
        
    context = {
        'pageSection': "teams",
        'person': person,
        'join_form': join_form,
        'profile_form': profile_form,
        'messages': messages
    }
    return render_to_response('people/person_detail.html', context, context_instance=RequestContext(request))

