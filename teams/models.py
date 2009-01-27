# -*- coding: utf-8 -*-
#
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

from django.db import models
from django.utils.translation import ugettext_lazy, ugettext as _
from people.models import Person

class TeamManager(models.Manager):
    def all_with_roles(self):
        """ This method prefills team.coordinator/committers/reviewers/translators to reduce subsequent database access"""
        teams = self.all()
        roles = Role.objects.select_related("person").all()
        role_dict = {}
        for role in roles:
            if role.team_id not in role_dict:
                role_dict[role.team_id] = [role]
            else:
                role_dict[role.team_id].append(role)
        for team in teams:
            if team.id in role_dict:
                for role in role_dict[team.id]:
                    team.fill_role(role.role, role.person)
        return teams


class Team(models.Model):
    """The lang_code is generally used for the name of the team."""

    name = models.CharField(max_length=80)
    description = models.TextField()
    members = models.ManyToManyField(Person, through='Role', related_name='teams')
    webpage_url = models.URLField(null=True, blank=True)
    mailing_list = models.EmailField(null=True, blank=True)
    mailing_list_subscribe = models.URLField(null=True, blank=True)
    objects = TeamManager()

    class Meta:
        db_table = 'team'
        ordering = ('description',)

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.roles = None

    def __unicode__(self):
        return self.description

    @models.permalink
    def get_absolute_url(self):
        return ('team_slug', [self.name])
    
    def fill_role(self, role, person):
        """ Used by TeamManager to prefill roles in team """
        if not self.roles:
            self.roles = {'coordinator':[], 'committer':[], 'reviewer':[], 'translator':[]}
        self.roles[role].append(person)
        
    def get_description(self):
        return _(self.description)
    
    def get_languages(self):
        return self.language_set.all()

    def get_coordinator(self):
        try:
            return self.roles['coordinator'][0]
        except:
            # The join by role__team__id generates only one query and
            # the same one by role__team=self two queries!
            return Person.objects.get(role__team__id=self.id, role__role='coordinator')

    def get_members_by_role(self, role):
        try:
            return self.roles[role]
        except:
            members = Person.objects.filter(role__team__id=self.id, role__role=role)
            return members
        
    def get_committers(self):
        return self.get_members_by_role('committer')

    def get_reviewers(self):
        return self.get_members_by_role('reviewer')

    def get_translators(self):
        return self.get_members_by_role('translator')

class FakeTeam(object):
    """ This is a class replacing a Team object when a language
        has no team attached """
    fake = 1
    
    def __init__(self, language):
        self.language = language
        self.description = _("No team for locale %s") % self.language.locale
    
    def get_absolute_url(self):
        # FIXME: try to avoid using a hard-coded link 
        return "/teams/%s" % self.language.locale
    
    def get_description(self):
        return self.language.locale

    def get_languages(self):
        return (self.language,)
    
    def get_coordinator(self):
        return None


ROLE_CHOICES = (
    ('translator', ugettext_lazy('Translator')),
    ('reviewer', ugettext_lazy('Reviewer')),
    ('committer', ugettext_lazy('Committer')),
    ('coordinator', ugettext_lazy('Coordinator')),
)

class Role(models.Model):
    """ This is the intermediary class between Person and Team to attribute
        roles to Team members. """
    
    team = models.ForeignKey(Team)
    person = models.ForeignKey(Person)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='translator')

    class Meta:
        db_table = 'role'
        unique_together = ('team', 'person')
    
    def __unicode__(self):
        return "%s is %s in %s team" % (self.person.name, self.role, self.team.description)

