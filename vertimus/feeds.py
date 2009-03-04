# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 Stéphane Raimbault <stephane.raimbault@gmail.com>
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

from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from languages.models import Language
from teams.models import Team
from vertimus.models import ActionDb, ActionDbBackup
from common.utils import merge_sorted_by_field

class LatestActionsByLanguage(Feed):
    title_template = 'feeds/actions_title.html'
    description_template = 'feeds/actions_description.html'
    
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Language.objects.get(locale=bits[0])

    def title(self, obj):
        current_site = Site.objects.get_current()
        return _("%(site)s - Vertimus actions for the %(lang)s language") % {
                  'site': current_site, 'lang': obj.name }

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_team_url()

    def description(self, obj):
        return _("Latest actions of the GNOME Translation Project for the %s language") % obj.name

    def items(self, obj):
        # The Django ORM doesn't provide the UNION SQL feature :-(
        # so we need to fetch twice more objects than required
        actions_db = ActionDb.objects.filter(state_db__language=obj.id).select_related('state').order_by('-created')[:20]
        archived_actions_db = ActionDbBackup.objects.filter(state_db__language=obj.id).select_related('state').order_by('-created')[:20]

        return (action_db.get_action() for action_db in merge_sorted_by_field(actions_db, archived_actions_db, '-created')[:20])

    def item_link(self, item):
        return urlresolvers.reverse('vertimus-names-view', 
                                    args=(item.state.branch.module.name, 
                                          item.state.branch.name,
                                          item.state.domain.name,
                                          item.state.language.locale))

    def item_pubdate(self, item):
        return item.created

    def item_author_name(self, item):
        return item.person


class LatestActionsByTeam(Feed):
    title_template = 'feeds/actions_title.html'
    description_template = 'feeds/actions_description.html'

    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Team.objects.get(name=bits[0])

    def title(self, obj):
        current_site = Site.objects.get_current()
        return _("%(site)s - Vertimus actions of the %(lang)s team") % {
                  'site': current_site, 'lang': obj}

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return _("Latest actions made by the %s team of the GNOME Translation Project") % obj

    def items(self, obj):
        # The Django ORM doesn't provide the UNION SQL feature :-(
        # so we need to fetch twice more objects than required
        actions_db = ActionDb.objects.filter(state_db__language__team=obj.id).select_related('state').order_by('-created')[:20]
        archived_actions_db = ActionDbBackup.objects.filter(state_db__language__team=obj.id).select_related('state').order_by('-created')[:20]

        return (action_db.get_action() for action_db in merge_sorted_by_field(actions_db, archived_actions_db, '-created')[:20])

    def item_link(self, item):
        return urlresolvers.reverse('vertimus-names-view', 
                                    args=(item.state.branch.module.name, 
                                          item.state.branch.name,
                                          item.state.domain.name,
                                          item.state.language.locale))

    def item_pubdate(self, item):
        return item.created

    def item_author_name(self, item):
        return item.person
