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

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from common import utils
from teams.models import Team, FakeTeam
from languages.models import Language

def teams(request):
    teams = Team.objects.all()

    context = {
        'pageSection': 'teams',              
        'teams': utils.trans_sort_object_list(teams, 'description') 
    }
    return render_to_response('teams/team_list.html', context, context_instance=RequestContext(request))

def team(request, team_slug):
    try:
        team = Team.objects.get(name=team_slug)
    except:
        lang = get_object_or_404(Language, locale=team_slug)
        team = FakeTeam(lang)
    
    context = {
        'pageSection': 'teams',
        'team': team
    }
    return render_to_response('teams/team_detail.html', context, context_instance=RequestContext(request))
       
