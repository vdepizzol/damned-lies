# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>
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

import os

from datetime import datetime
from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core import mail, urlresolvers
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.files.storage import default_storage

from stats.models import Branch, Domain
from languages.models import Language
from people.models import Person

#
# States
#

# Sadly, the Django ORM isn't as powerful than SQLAlchemy :-(
# So we need to use composition with StateDB and State to obtain
# the desired behaviour.
class StateDb(models.Model):
    """Database storage of a State"""
    branch = models.ForeignKey(Branch)
    domain = models.ForeignKey(Domain)
    language = models.ForeignKey(Language)
    person = models.ForeignKey(Person, default=None, null=True)
    
    name = models.SlugField(max_length=20, default='None')
    updated = models.DateTimeField(default=datetime.now, editable=False)

    class Meta:
        db_table = 'state'
        unique_together = ('branch', 'domain', 'language')

    def get_state(self):
        state = eval('State'+self.name)()
        state._state_db = self
        return state

    def __unicode__(self):
        return self.name

class StateAbstract(object):
    """Abstract class"""

    @property
    def branch(self):
        return self._state_db.branch

    @property
    def domain(self):
        return self._state_db.domain

    @property
    def language(self):
        return self._state_db.language

    def get_person(self):
        return self._state_db.person

    def set_person(self, person):
        self._state_db.person = person
    person = property(get_person, set_person)

    @property
    def updated(self):
        return self._state_db.updated

    def get_state_db(self):
        return self._state_db

    def __unicode__(self):
        return unicode(self.description)

    def _get_available_actions(self, action_names):
        action_names.append('WC')
        return [eval('Action' + action_name)() for action_name in action_names]

    def apply_action(self, action, person, comment=None, file=None):
        if action.name in (a.name for a in self.get_available_actions(person)):
            new_state = action.apply(self, person, comment, file)
            if new_state != None:
                # Reuse the current state_db
                new_state._state_db = self._state_db
                # Only the name and the person change
                new_state._state_db.name = new_state.name
                new_state._state_db.person = person
                return new_state
            else:
                return self
        else:
            raise Exception('Not allowed')

    def save(self):
        self._state_db.save()


class StateNone(StateAbstract):
    name = 'None'
    description = _('Inactive')

    def get_available_actions(self, person):
        action_names = []

        if person.is_translator(self.language.team):
            action_names = ['RT']

        return self._get_available_actions(action_names)


class StateTranslating(StateAbstract):
    name = 'Translating'
    description = _('Translating') 

    def get_available_actions(self, person):
        action_names = []

        if (self.person == person):
            action_names = ['UT', 'UNDO']
                    
        return self._get_available_actions(action_names)


class StateTranslated(StateAbstract):
    name = 'Translated'
    description = _('Translated')

    def get_available_actions(self, person):
        action_names = []

        if person.is_reviewer(self.language.team):
            action_names.append('RP')

        if person.is_translator(self.language.team):
            action_names.append('RT')
            action_names.append('TR')

        return self._get_available_actions(action_names)


class StateProofreading(StateAbstract):
    name = 'Proofreading'
    description = _('Proofreading')

    def get_available_actions(self, person):
        action_names = []
        
        if person.is_reviewer(self.language.team):
            if (self.person == person):
                action_names = ['UP', 'TR', 'TC', 'UNDO']
                    
        return self._get_available_actions(action_names)


class StateProofread(StateAbstract):
    name = 'Proofread'
    description = _('Proofread')

    def get_available_actions(self, person):
        if person.is_reviewer(self.language.team):
            action_names = ['TC', 'TR']
        else:
            action_names = []

        return self._get_available_actions(action_names)


class StateToReview(StateAbstract):
    name = 'ToReview'
    description = _('To Review')

    def get_available_actions(self, person):
        action_names = []
        if person.is_translator(self.language.team):
            action_names.append('RT')

        return self._get_available_actions(action_names)


class StateToCommit(StateAbstract):
    name = 'ToCommit'
    description = _('To Commit')

    def get_available_actions(self, person):
        if person.is_committer(self.language.team):
            action_names = ['RC', 'TR']
        else:
            action_names = []
            
        return self._get_available_actions(action_names)


class StateCommitting(StateAbstract):
    name = 'Committing'
    description = _('Committing')
        
    def get_available_actions(self, person):
        action_names = []

        if person.is_committer(self.language.team):
            if (self.person == person):
                action_names = ['IC', 'TR', 'UNDO']
            
        return self._get_available_actions(action_names)


class StateCommitted(StateAbstract):
    name = 'Committed'
    description = _('Committed')

    def get_available_actions(self, person):
        if person.is_committer(self.language.team):
            action_names = ['BA']
        else:            action_names = []

        return self._get_available_actions(action_names)

#
# Actions 
#


ACTION_NAMES = (
    'WC',
    'RT', 'UT',
    'RP', 'UP',
    'TC', 'RC',
    'IC', 'TR',
    'BA', 'UNDO')

def generate_upload_file_name(instance, original_filename):
    filename = "%s-%s-%s-%s-%s.po" % (instance.state_db.branch.module.name, 
                                   instance.state_db.branch.name, 
                                   instance.state_db.domain.name,
                                   instance.state_db.language.locale,
                                   instance.state_db.id)
    return "%s/%s" % (settings.UPLOAD_DIR, filename)

class ActionDb(models.Model):
    state_db = models.ForeignKey(StateDb)
    person = models.ForeignKey(Person)

    name = models.SlugField(max_length=8)
    description = None
    created = models.DateTimeField(auto_now_add=True, editable=False)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=generate_upload_file_name, blank=True, null=True)

    class Meta:
        db_table = 'action'
        ordering = ('-created',)

    def get_action(self):
        action = eval('Action' + self.name)()
        action._action_db = self
        return action

    @classmethod
    def get_action_history(cls, state_db):
        if state_db:
            return [va_db.get_action() for va_db in ActionDb.objects.filter(
                    state_db__id=state_db.id).order_by('created')]
        else:
            return []

    def __unicode__(self):
        return self.name
    

class ActionAbstract(object):
    """Abstract class"""

    # A comment or a file is required
    arg_is_required = False
    file_is_required = False
    
    @classmethod
    def new_by_name(cls, action_name):
         return eval('Action' + action_name)()

    @classmethod
    def get_all(cls):
        """Reserved to the admins to access all actions"""
        return [eval('Action' + action_name)() for action_name in ACTION_NAMES]

    @property
    def person(self):
        return self._action_db.person

    @property
    def comment(self):
        return self._action_db.comment

    @property
    def created(self):
        return self._action_db.created

    @property
    def file(self):
        return self._action_db.file

    def save_action_db(self, state, person, comment=None, file=None):
        """Used by apply"""
        self._action_db = ActionDb(state_db=state._state_db,
            person=person, name=self.name, comment=comment, file=file)
        if file:
            self._action_db.file.save(file.name, file, save=False)
        self._action_db.save()

    def __unicode__(self):
        return unicode(self.description) # needs unicode() because description is lazy
    
    def get_filename(self):
        if self._action_db.file:
            return os.path.basename(self._action_db.file.name)
        else:
            return None

    def send_mail_new_state(self, old_state, new_state, recipient_list):
        # Remove None and empty string items from the list
        recipient_list = filter(lambda x: x and x is not None, recipient_list)

        if recipient_list:
            current_site = Site.objects.get_current()
            url = "http://%s%s" % (current_site.domain, urlresolvers.reverse(
                'vertimus-names-view',
                 args = (
                    old_state.branch.module.name,
                    old_state.branch.name,
                    old_state.domain.name,
                    old_state.language.locale)))
            subject = old_state.branch.module.name + u' - ' + old_state.branch.name
            message = _(u"""Hello,

The new state of %(module)s - %(branch)s - %(domain)s (%(language)s) is now '%(new_state)s'.
%(url)s

""") % { 
                'module': old_state.branch.module.name,
                'branch': old_state.branch.name,
                'domain': old_state.domain.name,
                'language': old_state.language.name, 
                'new_state': new_state, 
                'url': url
            }
            message += self.comment or ugettext("Without comment")
            message += "\n\n" + self.person.name
            mail.send_mail(subject, message, self.person.email, recipient_list)

class ActionWC(ActionAbstract):
    name = 'WC'
    description = _('Write a comment')
    arg_is_required = True

    def _new_state(self):
        return None

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        # Send an email to all translators of the page
        translator_emails = set()
        for d in Person.objects.filter(actiondb__state_db=state.get_state_db()).values('email'):
            translator_emails.add(d['email'])

        # Remove None items from the list
        translator_emails = filter(lambda x: x is not None, translator_emails)

        if translator_emails:
            current_site = Site.objects.get_current()
            url = "http://%s%s" % (current_site.domain, urlresolvers.reverse(
                'vertimus-names-view',
                args = (
                    state.branch.module.name,
                    state.branch.name,
                    state.domain.name,
                    state.language.locale)))
            subject = state.branch.module.name + u' - ' + state.branch.name
            message = _(u"""Hello,

A new comment has been left on %(module)s - %(branch)s - %(domain)s (%(language)s).
%(url)s

""") % { 
                'module': state.branch.module.name,
                'branch': state.branch.name,
                'domain': state.domain.name,
                'language': state.language.name, 
                'url': url
            }
            message += comment or ugettext("Without comment")
            message += "\n" + person.name
            mail.send_mail(subject, message, person.email, translator_emails)

        return self._new_state()

class ActionRT(ActionAbstract):
    name = 'RT'
    description = _('Reserve for translation')

    def _new_state(self):
        return StateTranslating()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        return self._new_state()

class ActionUT(ActionAbstract):
    name = 'UT'
    description = _('Upload the new translation')
    file_is_required = True

    def _new_state(self):
        return StateTranslated()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        new_state = self._new_state()
        self.send_mail_new_state(state, new_state, (state.language.team.mailing_list,))
        return new_state

class ActionRP(ActionAbstract):
    name = 'RP'
    description = _('Reserve for proofreading')

    def _new_state(self):
        return StateProofreading()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        return self._new_state()

class ActionUP(ActionAbstract):
    name = 'UP'
    description = _('Upload for proofreading')
    file_is_required = True

    def _new_state(self):
        return StateProofread()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        new_state = self._new_state()
        self.send_mail_new_state(state, new_state, (state.language.team.mailing_list,))
        return new_state

class ActionTC(ActionAbstract):
    name = 'TC'
    description = _('Ready for submission')

    def _new_state(self):
        return StateToCommit()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        new_state = self._new_state()
        # Send an email to all committers of the team
        committers = [c.email for c in state.language.team.get_committers()]
        self.send_mail_new_state(state, new_state, committers)
        return new_state

class ActionRC(ActionAbstract):
    name = 'RC'
    description = _('Reserve to submit')

    def _new_state(self):
        return StateCommitting()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        return self._new_state()

class ActionIC(ActionAbstract):
    name = 'IC'
    description = _('Inform of submission')

    def _new_state(self):
        return StateCommitted()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        new_state = self._new_state()
        self.send_mail_new_state(state, new_state, (state.language.team.mailing_list,))
        return new_state

class ActionTR(ActionAbstract):
    name = 'TR'
    description = _('Requiring review')
    arg_is_required = True

    def _new_state(self):
        return StateToReview()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        new_state = self._new_state()
        self.send_mail_new_state(state, new_state, (state.language.team.mailing_list,))
        return new_state

def generate_backup_file_name(instance, original_filename):
    return "%s/%s" % (settings.UPLOAD_BACKUP_DIR, original_filename)

class ActionDbBackup(models.Model):
    state_db = models.ForeignKey(StateDb)
    person = models.ForeignKey(Person)

    name = models.SlugField(max_length=8)
    created = models.DateField(auto_now_add=True, editable=False)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=generate_backup_file_name, blank=True, null=True)
    sequence = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'action_backup'

class ActionBA(ActionAbstract):
    name = 'BA'
    description = _('Backup the actions')

    def _new_state(self):
        return StateNone()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        actions_db = ActionDb.objects.filter(state_db=state._state_db).all()

        sequence = None
        for action_db in actions_db:
            file_to_backup = None
            if action_db.file:
                file_to_backup = action_db.file.file # get a file object, not a filefield
            action_db_backup = ActionDbBackup(
                state_db=action_db.state_db,
                person=action_db.person,
                name=action_db.name,
                created=action_db.created,
                comment=action_db.comment,
                file=file_to_backup)
            if file_to_backup:
                action_db_backup.file.save(self.get_filename(), file_to_backup, save=False)
            action_db_backup.save()

            if sequence == None:
                sequence = action_db_backup.id
                action_db_backup.sequence = sequence
                action_db_backup.save()

            action_db.delete() # The file is also automatically deleted, if it is not referenced elsewhere           

        return self._new_state()

class ActionUNDO(ActionAbstract):
    name = 'UNDO'
    description = _('Undo the last state change')
    
    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        try:
            # Exclude himself
            action_db = ActionDb.objects.filter(state_db__id=state._state_db.id).exclude(
                name__in=['WC', 'UNDO']).order_by('-created')[1]
            action = action_db.get_action()
            return action._new_state()
        except:
            return StateNone()
