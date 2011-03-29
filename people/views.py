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

from operator import itemgetter

from django.conf import settings
from django.conf.locale import LANG_INFO
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import formats
from django.utils.translation import ugettext_lazy, ugettext as _

from people.models import Person
from teams.models import Team, Role
from people.forms import TeamJoinForm, DetailForm
from vertimus.models import StateDb

def person_detail(request, person_id=None, person_username=None):
    if person_id:
        person = get_object_or_404(Person, pk=person_id)
    else:
        person = get_object_or_404(Person, username=person_username)

    states = StateDb.objects.filter(actiondb__person=person).distinct()
    all_languages = [(lg[0], LANG_INFO.get(lg[0], {'name_local': lg[1]})['name_local']) for lg in settings.LANGUAGES]
    all_languages.sort(key=itemgetter(1))
    context = {
        'pageSection': "teams",
        'all_languages': all_languages,
        'person': person,
        'on_own_page': request.user.is_authenticated() and person.username == request.user.username,
        'states': states,
        'dateformat': formats.get_format('DATE_FORMAT'),
    }
    return render_to_response('people/person_detail.html', context,
            context_instance=RequestContext(request))

@login_required
def person_detail_change(request):
    """Handle the form to change the details"""
    person = get_object_or_404(Person, username=request.user.username)
    if request.method == 'POST':
        form = DetailForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
        else:
            messages.error(request, _("Sorry, the form is not valid."))
    else:
        form = DetailForm(instance=person)

    context = {
        'pageSection': "teams",
        'person': person,
        'on_own_page': person.username == request.user.username,
        'form': form,
    }
    return render_to_response('people/person_detail_change_form.html', context,
            context_instance=RequestContext(request))

@login_required
def person_team_join(request):
    """Handle the form to join a team"""
    person = get_object_or_404(Person, username=request.user.username)
    if request.method == 'POST':
        form = TeamJoinForm(request.POST)
        if form.is_valid():
            team = form.cleaned_data['teams']
            # Role default to 'translator'
            new_role = Role(team=team, person=person)
            try:
                new_role.save()
                messages.success(request, _("You have successfully joined the team '%s'.") % team.get_description())
                team.send_mail_to_coordinator(subject=ugettext_lazy("A new person joined your team"),
                                              message=ugettext_lazy("%(name)s has just joined your translation team on %(site)s"),
                                              messagekw = {'name': person.name, 'site': Site.objects.get_current()})
            except IntegrityError:
                messages.info(request, _("You are already member of this team."))
    else:
        form = TeamJoinForm()

    context = {
        'pageSection': "teams",
        'person': person,
        'on_own_page': person.username == request.user.username,
        'form': form,
    }

    context_instance = RequestContext(request)
    return render_to_response('people/person_team_join_form.html', context,
            context_instance=context_instance)

@login_required
def person_team_leave(request, team_slug):
    person = get_object_or_404(Person, username=request.user.username)
    team = get_object_or_404(Team, name=team_slug)
    try:
        role = Role.objects.get(team=team, person=person)
        role.delete()
        messages.success(request, _("You have been removed from the team '%s'.") % team.get_description())
    except Role.DoesNotExist:
        # Message no i18n'ed, should never happen under normal conditions
        messages.error(request, _("You are not a member of this team."))
    # redirect to normal person detail
    return HttpResponseRedirect(urlresolvers.reverse('person_detail_username',
                                                     args=(person.username,)))

@login_required
def person_password_change(request):
    """Handle the generic form to change the password"""
    person = get_object_or_404(Person, username=request.user.username)

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            messages.success(request, _("Your password has been changed."))
            form.save()
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'pageSection': "teams",
        'person': person,
        'on_own_page': person.username == request.user.username,
        'form': form,
    }
    return render_to_response('people/person_password_change_form.html', context,
            context_instance=RequestContext(request))
