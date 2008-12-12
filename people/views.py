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
from django.template import RequestContext
from people.models import Person
from teams.models import Role
from people.forms import JoinTeamForm

def person_detail_from_username(request, slug):
    person = get_object_or_404(Person, username=slug)
    return person_detail(request, person)

def person_detail_from_id(request, object_id):
    person = get_object_or_404(Person, pk=object_id)
    return person_detail(request, person)

def person_detail(request, person):
    if request.method == 'POST':
        form = JoinTeamForm(request.POST)
        if form.is_valid():
            if request.user.username == person.username:
                team = form.cleaned_data['teams']
                new_role = Role(team=team, person=person) # role default to translator
                new_role.save()
            else:
                messages.append("Sorry, you're not allowed to modify this user.")
    else:
        form = JoinTeamForm()
    context = {
        'pageSection': "teams",
        'person': person,
        'form': form
    }
    return render_to_response('people/person_detail.html', context, context_instance=RequestContext(request))

