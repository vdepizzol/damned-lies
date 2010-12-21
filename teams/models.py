# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>.
# Copyright (c) 2009 Claude Paroz <claude@2xlibre.net>
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

from datetime import datetime, timedelta

from django.db import models
from django.core import mail
from django.utils import translation
from django.utils.translation import ugettext_lazy, ugettext as _
from django.conf import settings
from django.contrib.sites.models import Site
from people.models import Person

class TeamManager(models.Manager):

    def all_with_coordinator(self):
        """
        Returns all teams with the coordinator already prefilled. Use that
        function to reduce the size of extracted data and the numbers of objects
        built or use all_with_roles() if you need informations about the other
        roles.
        """
        teams = self.all()
        roles = Role.objects.select_related("person").filter(role='coordinator',
                                                                is_active=True)
        role_dict = {}

        for role in roles:
            # Only one coordinator by team
            role_dict[role.team_id] = role

        for team in teams:
            try:
                role = role_dict[team.id]
                team.roles = {'coordinator': [role.person]}
            except KeyError:
                # Abnormal because a team must have a coordinator but of no
                # consequence
                pass
        return teams

    def all_with_roles(self):
        """
        This method prefills team.coordinator/committer/reviewer/translator to
        reduce subsequent database access.
        """
        teams = self.all()
        roles = Role.objects.select_related("person").filter(is_active=True)
        role_dict = {}

        for role in roles:
            if role.team_id not in role_dict:
                role_dict[role.team_id] = [role]
            else:
                role_dict[role.team_id].append(role)

        for team in teams:
            try:
                for role in role_dict[team.id]:
                    team.fill_role(role.role, role.person)
            except KeyError:
                # Abnormal because a team must have a coordinator but of no
                # consequence
                pass
        return teams


class Team(models.Model):
    """The lang_code is generally used for the name of the team."""

    name = models.CharField(max_length=80)
    description = models.TextField()
    use_workflow = models.BooleanField(default=True)
    presentation = models.TextField(blank=True, verbose_name=_("Presentation"))
    members = models.ManyToManyField(Person, through='Role', related_name='teams')
    webpage_url = models.URLField(null=True, blank=True, verbose_name=_("Web page"))
    mailing_list = models.EmailField(null=True, blank=True, verbose_name=_("Mailing list"))
    mailing_list_subscribe = models.URLField(null=True, blank=True, verbose_name=_("URL to subscribe"))
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

    def can_edit(self, user):
        """ Return True if user is allowed to edit this team
            user is a User (from request.user), not a Person
        """
        coordinator = self.get_coordinator()
        return user.is_authenticated() and coordinator and user.username == coordinator.username

    def fill_role(self, role, person):
        """ Used by TeamManager to prefill roles in team """
        if not self.roles:
            self.roles = {'coordinator': [],
                          'committer': [],
                          'reviewer': [],
                          'translator': []}
        self.roles[role].append(person)

    def get_description(self):
        return _(self.description)

    def get_languages(self):
        return self.language_set.all()

    def get_coordinator(self):
        try:
            return self.roles['coordinator'][0]
        except:
            try:
                # The join by role__team__id generates only one query and
                # the same one by role__team=self two queries!
                return Person.objects.get(role__team__id=self.id,
                                          role__role='coordinator')
            except Person.DoesNotExist:
                return None

    def get_members_by_role_exact(self, role):
        """ Return a list of active members """
        try:
            return self.roles[role]
        except:
            members = list(Person.objects.filter(role__team__id=self.id,
                                                 role__role=role,
                                                 role__is_active=True))
            return members

    def get_committers_exact(self):
        return self.get_members_by_role_exact('committer')

    def get_reviewers_exact(self):
        return self.get_members_by_role_exact('reviewer')

    def get_translators_exact(self):
        return self.get_members_by_role_exact('translator')

    def get_members_by_roles(self, roles):
        """Requires a list of roles in argument"""
        try:
            members = []
            for role in roles:
                members += self.roles[role]
        except:
            members = list(Person.objects.filter(role__team__id=self.id,
                                                 role__role__in=roles,
                                                 role__is_active=True))
        return members

    def get_committers(self):
        return self.get_members_by_roles(['coordinator', 'committer'])

    def get_reviewers(self):
        return self.get_members_by_roles(['coordinator', 'committer', 'reviewer'])

    def get_translators(self):
        """Don't use get_members_by_roles to provide an optimization"""
        try:
            members = []
            for role in ['coordinator', 'committer', 'reviewer', 'translator']:
                members += self.roles[role]
        except:
            # Not necessary to filter as for other roles
            members = list(self.members.all())
        return members

    def get_inactive_members(self):
        """ Return the inactive members """
        members = list(Person.objects.filter(role__team__id=self.id,
                                             role__is_active=False)) 
        return members

    def send_mail_to_coordinator(self, subject, message, messagekw={}):
        """ Send a message to the coordinator, in her language if available
            and if subject and message are lazy strings """
        coordinator = self.get_coordinator()
        if not coordinator or not coordinator.email:
            return
        prev_lang = translation.get_language()
        translation.activate(self.language_set.all()[0].locale)

        message = u"%s\n--\n" % (message % messagekw,)
        message += _(u"This is an automated message sent from %s.") % Site.objects.get_current()
        mail.send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [coordinator.email]
        )
        translation.activate(prev_lang)

class FakeTeam(object):
    """
    This is a class replacing a Team object when a language
    has no team attached.
    """
    fake = 1

    def __init__(self, language):
        self.language = language
        self.description = _("No team for locale %s") % self.language.locale

    @models.permalink
    def get_absolute_url(self):
        return ('teams.views.team', [self.language.locale])

    def can_edit(self, user):
        return False

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
    """
    This is the intermediary class between Person and Team to attribute roles to
    Team members.
    """
    team = models.ForeignKey(Team)
    person = models.ForeignKey(Person)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES,
                            default='translator')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'role'
        unique_together = ('team', 'person')

    def __unicode__(self):
        return "%s is %s in %s team" % (self.person.name, self.role,
                                        self.team.description)

    @classmethod
    def inactivate_unused_roles(cls):
         """ Inactivate the roles when login older than 180 days  """
         last_login = datetime.now() - timedelta(days=30*6)
         cls.objects.filter(person__last_login__lt=last_login,
                            is_active=True).update(is_active=False)
