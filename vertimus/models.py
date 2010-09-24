# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2009 Stéphane Raimbault <stephane.raimbault@gmail.com>
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

import os, sys

from django.db import models
from django.utils.translation import get_language, activate, ugettext, ugettext_lazy as _
from django.core import mail, urlresolvers
from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.db import connection

from stats.models import Branch, Domain, Statistics
from stats.signals import pot_has_changed
from stats.utils import run_shell_command
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
    updated = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)

    class Meta:
        db_table = 'state'
        unique_together = ('branch', 'domain', 'language')

    def get_state(self):
        state = eval('State'+self.name)()
        state._state_db = self
        return state

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('vertimus_by_ids', [self.branch.id, self.domain.id, self.language.id])

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

    def _get_available_actions(self, person, action_names):
        action_names.append('WC')
        if person.is_committer(self.language.team) and 'IC' not in action_names:
            action_names.extend(('Separator', 'IC'))
            if self.name not in ('None', 'Committed'):
                action_names.append('AA')
        return [eval('Action' + action_name)() for action_name in action_names]

    def apply_action(self, action, person, comment=None, file=None):
        # Check the permission to use this action
        if action.name in (a.name for a in self.get_available_actions(person)):
            new_state = action.apply(self, person, comment, file)
            if new_state != None:
                # Reuse the current state_db
                new_state._state_db = self._state_db
                # Only the name and the person change
                new_state._state_db.name = new_state.name
                new_state._state_db.person = person

                if isinstance(new_state, StateCommitted):
                    # Committed is the last state of the workflow
                    new_state.save()

                    # Archive actions
                    return new_state.apply_action(ActionAA(), person)

                return new_state
            else:
                return self
        else:
            raise Exception('Not allowed')

    def get_action_sequence_from_level(self, level):
        """Get the sequence corresponding to the requested level.
           The first level is 1."""
        if level <= 0:
            raise Exception("Level must be greater than 0")

        # Raw SQL in waiting for Django 1.1.
        query = """
            SELECT sequence
              FROM action_archived
             WHERE state_db_id = %s
             GROUP BY sequence
             ORDER BY sequence DESC
             LIMIT 1 OFFSET %s"""
        cursor = connection.cursor()
        cursor.execute(query, (self._state_db.id, level - 1))
        try:
            sequence = cursor.fetchone()[0]
        except:
            sequence = None

        return sequence

    def save(self):
        self._state_db.save()


class StateNone(StateAbstract):
    name = 'None'
    description = _('Inactive')

    def get_available_actions(self, person):
        action_names = []

        if person.is_translator(self.language.team) or person.is_maintainer_of(self.branch.module):
            action_names = ['RT']

        return self._get_available_actions(person, action_names)


class StateTranslating(StateAbstract):
    name = 'Translating'
    description = _('Translating')

    def get_available_actions(self, person):
        action_names = []

        if (self.person == person):
            action_names = ['UT', 'UNDO']

        return self._get_available_actions(person, action_names)


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

        return self._get_available_actions(person, action_names)


class StateProofreading(StateAbstract):
    name = 'Proofreading'
    description = _('Proofreading')

    def get_available_actions(self, person):
        action_names = []

        if person.is_reviewer(self.language.team):
            if (self.person == person):
                action_names = ['UP', 'TR', 'TC', 'UNDO']

        return self._get_available_actions(person, action_names)


class StateProofread(StateAbstract):
    name = 'Proofread'
    # Translators: This is a status, not a verb
    description = _('Proofread')

    def get_available_actions(self, person):
        if person.is_reviewer(self.language.team):
            action_names = ['TC', 'RP', 'TR']
        else:
            action_names = []
        if not self.branch.is_vcs_readonly() and person.is_committer(self.language.team):
            action_names.insert(1, 'CI')

        return self._get_available_actions(person, action_names)


class StateToReview(StateAbstract):
    name = 'ToReview'
    description = _('To Review')

    def get_available_actions(self, person):
        action_names = []
        if person.is_translator(self.language.team):
            action_names.append('RT')

        return self._get_available_actions(person, action_names)


class StateToCommit(StateAbstract):
    name = 'ToCommit'
    description = _('To Commit')

    def get_available_actions(self, person):
        if person.is_committer(self.language.team):
            action_names = ['RC', 'TR']
            if not self.branch.is_vcs_readonly():
                action_names.insert(1, 'CI')
        else:
            action_names = []

        return self._get_available_actions(person, action_names)


class StateCommitting(StateAbstract):
    name = 'Committing'
    description = _('Committing')

    def get_available_actions(self, person):
        action_names = []

        if person.is_committer(self.language.team):
            if (self.person == person):
                action_names = ['IC', 'TR', 'UNDO']

        return self._get_available_actions(person, action_names)


class StateCommitted(StateAbstract):
    name = 'Committed'
    description = _('Committed')

    def get_available_actions(self, person):
        if person.is_committer(self.language.team):
            action_names = ['AA']
        else:
            action_names = []

        return self._get_available_actions(person, action_names)

#
# Actions
#

ACTION_NAMES = (
    'WC',
    'RT', 'UT',
    'RP', 'UP',
    'TC', 'CI', 'RC',
    'IC', 'TR',
    'AA', 'UNDO')

def generate_upload_filename(instance, filename):
    # Extract the first extension (with the point)
    root, ext = os.path.splitext(filename)
    # Check if a second extension is present
    if os.path.splitext(root)[1] == ".tar":
        ext = ".tar" + ext
    new_filename = "%s-%s-%s-%s-%s%s" % (
        instance.state_db.branch.module.name,
        instance.state_db.branch.name,
        instance.state_db.domain.name,
        instance.state_db.language.locale,
        instance.state_db.id,
        ext)
    return "%s/%s" % (settings.UPLOAD_DIR, new_filename)

def action_db_get_action_history(cls, state_db=None, sequence=None):
    """
    Return action history as a list of tuples (action, file_history),
    file_history is a list of previous po files, used in vertimus view to
    generate diff links
    """
    history = []
    if state_db or sequence:
        file_history = [{'action_id':0, 'title': ugettext("File in repository")}]
        if not sequence:
            query = cls.objects.filter(state_db__id=state_db.id)
        else:
            # Not necessary to filter on state_db with a sequence (unique)
            query = cls.objects.filter(sequence=sequence)
        for action_db in query.order_by('id'):
            history.append((action_db.get_action(), list(file_history)))
            if action_db.file and action_db.file.path.endswith('.po'):
                # Action.id and ActionDb.id are identical (inheritance)
                file_history.insert(0, {
                    'action_id': action_db.id,
                    'title': ugettext("Uploaded file by %(name)s on %(date)s") % {
                        'name': action_db.person.name,
                        'date': action_db.created },
                    })
    return history

class ActionDb(models.Model):
    state_db = models.ForeignKey(StateDb)
    person = models.ForeignKey(Person)

    name = models.SlugField(max_length=8)
    description = None
    created = models.DateTimeField(auto_now_add=True, editable=False)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=generate_upload_filename, blank=True, null=True)

    class Meta:
        db_table = 'action'

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.id)

    def get_action(self):
        action = eval('Action' + self.name)()
        action._action_db = self
        return action

    def get_previous_action_db_with_po(self):
        """
        Return the previous ActionDb with an uploaded file related to the
        same state.
        """
        try:
            action_db = ActionDb.objects.filter(file__endswith=".po", state_db=self.state_db,
                id__lt=self.id).latest('id')
            return action_db
        except ActionDb.DoesNotExist:
            return None

    def merge_file_with_pot(self, pot_file):
        """Merge the uploaded translated file with current pot."""
        if self.file:
            command = "msgmerge --previous -o %(out_po)s %(po_file)s %(pot_file)s" % {
                'out_po': self.file.path[:-3] + ".merged.po",
                'po_file': self.file.path,
                'pot_file': pot_file
            }
            run_shell_command(command)

    @classmethod
    def get_action_history(cls, state_db):
        return action_db_get_action_history(cls, state_db=state_db)

def generate_archive_filename(instance, original_filename):
    return "%s/%s" % (settings.UPLOAD_ARCHIVED_DIR, os.path.basename(original_filename))

class ActionDbArchived(models.Model):
    state_db = models.ForeignKey(StateDb)
    person = models.ForeignKey(Person)

    name = models.SlugField(max_length=8)
    # Datetime copied from ActionDb
    created = models.DateTimeField(editable=False)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=generate_archive_filename, blank=True, null=True)
    # The first element of each cycle is null at creation time (and defined
    # afterward).
    sequence = models.IntegerField(null=True)

    class Meta:
        db_table = 'action_archived'

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.id)

    def get_action(self):
        action = eval('Action' + self.name)()
        action._action_db = self
        return action

    @classmethod
    def get_action_history(cls, sequence):
        return action_db_get_action_history(cls, state_db=None, sequence=sequence)

class ActionAbstract(object):
    """Abstract class"""

    # A comment or a file is required
    arg_is_required = False
    comment_is_required = False
    file_is_required = False
    file_is_prohibited = False

    @classmethod
    def new_by_name(cls, action_name):
         return eval('Action' + action_name)()

    @classmethod
    def get_all(cls):
        """Reserved to the admins to access all actions"""
        return [eval('Action' + action_name)() for action_name in ACTION_NAMES]

    @property
    def id(self):
        return self._action_db.id

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

    @property
    def state(self):
        return self._action_db.state_db.get_state()

    def get_previous_action_with_po(self):
        """
        Return the previous Action with an uploaded file related to the same
        state.
        """
        action_db = self._action_db.get_previous_action_db_with_po()
        if action_db:
            return action_db.get_action()
        else:
            return None

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

    def merged_file(self):
        """If available, returns the merged file as a dict: {'url':'path':'filename'}"""
        mfile_url = mfile_path = mfile_name = None
        if self._action_db.file:
            mfile_url = self._action_db.file.url[:-3] + ".merged.po"
            mfile_path = self._action_db.file.path[:-3] + ".merged.po"
            mfile_name = os.path.basename(mfile_path)
            if not os.access(mfile_path, os.R_OK):
                mfile_url = mfile_path =  mfile_name = None
        return {'url': mfile_url, 'path': mfile_path, 'filename': mfile_name}

    def has_po_file(self):
        try:
            return self._action_db.file.name[-3:] == ".po"
        except:
            return False

    def send_mail_new_state(self, old_state, new_state, recipient_list):
        # Remove None and empty string items from the list
        recipient_list = filter(lambda x: x and x is not None, recipient_list)

        if recipient_list:
            current_lang = get_language()
            activate(old_state.language.locale)
            current_site = Site.objects.get_current()
            url = "http://%s%s" % (current_site.domain, urlresolvers.reverse(
                'vertimus_by_names',
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
                'language': old_state.language.get_name(),
                'new_state': new_state,
                'url': url
            }
            message += self.comment or ugettext("Without comment")
            message += "\n\n" + self.person.name
            message += "\n--\n" + _(u"This is an automated message sent from %s.") % current_site.domain
            mail.send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            activate(current_lang)


class ActionWC(ActionAbstract):
    name = 'WC'
    description = _('Write a comment')
    comment_is_required = True

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
            current_lang = get_language()
            activate(state.language.locale)
            current_site = Site.objects.get_current()
            url = "http://%s%s" % (current_site.domain, urlresolvers.reverse(
                'vertimus_by_names',
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
                'language': state.language.get_name(),
                'url': url
            }
            message += comment or ugettext("Without comment")
            message += "\n\n" + person.name
            message += "\n--\n" + _(u"This is an automated message sent from %s.") % current_site.domain
            mail.send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, translator_emails)
            activate(current_lang)

        return self._new_state()

class ActionRT(ActionAbstract):
    name = 'RT'
    description = _('Reserve for translation')
    file_is_prohibited = True

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
    file_is_prohibited = True

    def _new_state(self):
        return StateProofreading()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        return self._new_state()

class ActionUP(ActionAbstract):
    name = 'UP'
    description = _('Upload the proofread translation')
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
    # Translators: this means the file is ready to be committed in repository
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

class ActionCI(ActionAbstract):
    name = 'CI'
    description = _('Submit to repository')
    file_is_prohibited = True

    def _new_state(self):
        return StateCommitted()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        action_with_po = self.get_previous_action_with_po()
        try:
            state.branch.commit_po(action_with_po.file.path, state.domain, state.language, person)
            new_state = self._new_state()
        except:
            # Commit failed, state unchanged
            person.message_set.create(message=_("The commit failed. The error was: '%s'") % sys.exc_info()[1])
            self._action_db.delete()
            new_state = state
        if state != new_state:
            self.send_mail_new_state(state, new_state, (state.language.team.mailing_list,))
        return new_state

class ActionRC(ActionAbstract):
    name = 'RC'
    # Translators: this indicates a committer is going to commit the file in the repository
    description = _('Reserve to submit')
    file_is_prohibited = True

    def _new_state(self):
        return StateCommitting()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        return self._new_state()

class ActionIC(ActionAbstract):
    name = 'IC'
    # Translators: this is used to indicate the file has been committed in the repository
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
    # Translators: regardless of the translation completion, this file need to be reviewed
    description = _('Review required')
    arg_is_required = True

    def _new_state(self):
        return StateToReview()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        new_state = self._new_state()
        self.send_mail_new_state(state, new_state, (state.language.team.mailing_list,))
        return new_state

class ActionAA(ActionAbstract):
    name = 'AA'
    description = _('Archive the actions')

    def _new_state(self):
        return StateNone()

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        actions_db = ActionDb.objects.filter(state_db=state._state_db).order_by('id').all()

        sequence = None
        for action_db in actions_db:
            file_to_archive = None
            if action_db.file:
                file_to_archive = action_db.file.file # get a file object, not a filefield
            action_db_archived = ActionDbArchived(
                state_db=action_db.state_db,
                person=action_db.person,
                name=action_db.name,
                created=action_db.created,
                comment=action_db.comment,
                file=file_to_archive)
            if file_to_archive:
                action_db_archived.file.save(action_db.file.name, file_to_archive, save=False)

            if sequence == None:
                # The ID is available after the save()
                action_db_archived.save()
                sequence = action_db_archived.id

            action_db_archived.sequence = sequence
            action_db_archived.save()

            action_db.delete() # The file is also automatically deleted, if it is not referenced elsewhere

        return self._new_state()

class ActionUNDO(ActionAbstract):
    name = 'UNDO'
    description = _('Undo the last state change')

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        # Exclude WC because this action is a noop on State
        actions_db = ActionDb.objects.filter(state_db__id=state._state_db.id).exclude(name='WC').order_by('-id')
        i = 0
        while (i < len(actions_db)):
            if actions_db[i].name == 'UNDO':
                # Skip Undo and the associated action
                i = i + 2
            else:
                # Found
                action = actions_db[i].get_action()
                return action._new_state()
        return StateNone()

class ActionSeparator(object):
    """ Fake action to add a separator in action menu """
    name = None
    description = "--------"

def update_uploaded_files(sender, **kwargs):
    """Callback to handle pot_file_changed signal"""
    actions = ActionDb.objects.filter(state_db__branch=kwargs['branch'],
                                      state_db__domain=kwargs['domain'],
                                      file__endswith=".po")
    for action in actions:
        action.merge_file_with_pot(kwargs['potfile'])
pot_has_changed.connect(update_uploaded_files)

def merge_uploaded_file(sender, instance, **kwargs):
    """
    post_save callback for ActionDb that automatically merge uploaded file
    with latest pot file.
    """
    if instance.file and instance.file.path.endswith('.po'):
        try:
            stat = Statistics.objects.get(branch=instance.state_db.branch, domain=instance.state_db.domain, language=None)
        except Statistics.DoesNotExist:
            return
        potfile = stat.po_path()
        instance.merge_file_with_pot(potfile)
post_save.connect(merge_uploaded_file, sender=ActionDb)

def delete_merged_file(sender, instance, **kwargs):
    """
    pre_delete callback for ActionDb that deletes the merged file from upload
    directory.
    """
    if instance.file and instance.file.path.endswith('.po'):
        merged_file = instance.file.path[:-3] + ".merged.po"
        if os.access(merged_file, os.W_OK):
             os.remove(merged_file)
pre_delete.connect(delete_merged_file, sender=ActionDb)

""" The following string is just reproduced from a template so as a translator comment
    can be added (comments are not supported in templates) """
# Translators: human_level is an ordinal expression ('1st',' 2nd',...)
# which should be localized in Django itself
dummy = ugettext("Archived Actions (%(human_level)s archived series)" % {'human_level':0})
