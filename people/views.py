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
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from people.models import Person
from teams.models import Role
from people.forms import TeamJoinForm, DetailForm
from vertimus.models import StateDb

def person_detail(request, person_id=None, person_username=None):
    if person_id:
        person = get_object_or_404(Person, pk=person_id)
    else:
        person = get_object_or_404(Person, username=person_username)

    states = StateDb.objects.filter(actiondb__person=person).distinct()
    context = {
        'pageSection': "teams",
        'person': person,
        'states': states,
    }
    return render_to_response('people/person_detail.html', context,
            context_instance=RequestContext(request))

@login_required
def person_detail_change(request):
    """Handle the form to change the details"""
    person = get_object_or_404(Person, username=request.user.username)
    messages = []
    if request.method == 'POST':
        form = DetailForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
        else:
            messages.append("Sorry, the form is not valid.")
    else:
        form = DetailForm(instance=person)

    context = {
        'pageSection': "teams",
        'person': person,
        'form': form,
        'messages': messages
    }
    return render_to_response('people/person_detail_change_form.html', context,
            context_instance=RequestContext(request))

@login_required
@transaction.commit_manually
def person_team_join(request):
    """Handle the form to join a team"""
    person = get_object_or_404(Person, username=request.user.username)
    messages = []
    if request.method == 'POST':
        form = TeamJoinForm(request.POST)
        if form.is_valid():
            team = form.cleaned_data['teams']
            new_role = Role(team=team, person=person) # role default to translator
            try:
                new_role.save()
                transaction.commit()
            except IntegrityError:
                transaction.rollback()
                messages.append(_("You are already member of this team."))
    else:
        form = TeamJoinForm()

    context = {
        'pageSection': "teams",
        'person': person,
        'form': form,
        'messages': messages
    }
    return render_to_response('people/person_team_join_form.html', context, 
            context_instance=RequestContext(request))


@login_required
def person_password_change(request):
    """Handle the generic form to change the password"""
    person = get_object_or_404(Person, username=request.user.username)
    messages = []

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            messages.append(_("Your password has been changed."))
            form.save()
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'pageSection': "teams",
        'person': person,
        'form': form,
        'messages': messages
    }
    return render_to_response('people/person_password_change_form.html', context,
            context_instance=RequestContext(request))
    
