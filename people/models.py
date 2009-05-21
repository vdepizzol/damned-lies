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

import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, UserManager

def obfuscate_email(email):
    if email:
        return email.replace('@', ' at ').replace('.', ' dot ')
    return ''

class Person(User):
    """ The User class of D-L. """

    svn_account = models.SlugField(max_length=20, null=True, blank=True)
    image = models.URLField(_("Image"), null=True, blank=True,
                            help_text=_("URL to an image file (.jpg, .png, ...) of an hackergotchi"))
    webpage_url = models.URLField(_("Web page"), null=True, blank=True)
    irc_nick = models.SlugField(_("IRC nickname"), max_length=20, null=True, blank=True)
    bugzilla_account = models.EmailField(_("Bugzilla account"), null=True, blank=True,
                                         help_text=_("This should be an email address, useful if not equal to 'email' field"))
    activation_key = models.CharField(max_length=40, null=True, blank=True)

    # Use UserManager to get the create_user method, etc.
    objects = UserManager()

    class Meta:
        db_table = 'person'
        ordering = ('username',)

    @classmethod
    def clean_unactivated_accounts(cls):
        accounts = cls.objects.filter(activation_key__isnull=False,
                                      date_joined__lt=(datetime.datetime.now()-datetime.timedelta(days=10))).exclude(activation_key='')
        for account in accounts:
            account.delete()

    def save(self):
        if not self.password or self.password == "!":
            self.password = None
            self.set_unusable_password()
        super(User, self).save()

    def activate(self):
        self.activation_key = None
        self.is_active = True
        self.save()

    def no_spam_email(self):
        return obfuscate_email(self.email)

    def no_spam_bugzilla_account(self):
        return obfuscate_email(self.bugzilla_account)

    @property
    def name(self):
        if self.first_name or self.last_name:
            return self.first_name + " " + self.last_name
        else:
            return self.username

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('person-username-view', [self.username])

    def coordinates_teams(self):
        from teams.models import Team
        return Team.objects.filter(role__person__id=self.id).all()

    def is_coordinator(self, team):
        try:
            self.role_set.get(team__id=team.id, role='coordinator')
            return True
        except:
            return False

    def is_committer(self, team):
        try:
            self.role_set.get(team__id=team.id, role__in=['committer', 'coordinator'])
            return True
        except:
            return False

    def is_reviewer(self, team):
        try:
            self.role_set.get(team__id=team.id, role__in=['reviewer', 'committer', 'coordinator'])
            return True
        except:
            return False

    def is_translator(self, team):
        try:
            self.role_set.get(team__id=team.id)
            return True
        except:
            return False

    def get_languages(self):
        all_teams = [role.team for role in self.role_set.select_related('team')]
        all_languages = []
        for team in all_teams:
            all_languages.extend(team.get_languages())
        return all_languages

    # Related names
    # - module: maintains_modules
