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
import shutil
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail, urlresolvers
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save, post_delete
from django.utils.translation import get_language, activate, ugettext, ugettext_lazy as _

from stats.models import Branch, Domain, Statistics, PoFile
from stats.signals import pot_has_changed
from stats.utils import run_shell_command, is_po_reduced, po_grep
from languages.models import Language
from people.models import Person

from teams.models import Role

#
# States
#

class State(models.Model):
    """State of a module translation"""
    branch = models.ForeignKey(Branch)
    domain = models.ForeignKey(Domain)
    language = models.ForeignKey(Language)
    person = models.ForeignKey(Person, default=None, null=True)

    name = models.SlugField(max_length=20, default='None')
    updated = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)

    class Meta:
        db_table = 'state'
        verbose_name = 'state'
        unique_together = ('branch', 'domain', 'language')

    def __init__(self, *args, **kwargs):
        super(State, self).__init__(*args, **kwargs)
        if self.name == 'None' and getattr(self.__class__, 'name', 'None') != 'None':
            self.name = self.__class__.name
        self.__class__ = {
            'None'        : StateNone,
            'Translating' : StateTranslating,
            'Translated'  : StateTranslated,
            'Proofreading': StateProofreading,
            'Proofread'   : StateProofread,
            'ToReview'    : StateToReview,
            'ToCommit'    : StateToCommit,
            'Committing'  : StateCommitting,
            'Committed'   : StateCommitted,
        }.get(self.name, State)

    def __unicode__(self):
        return "%s: %s %s (%s - %s)" % (self.name, self.branch.module.name,
            self.branch.name, self.language.name, self.domain.name)

    @models.permalink
    def get_absolute_url(self):
        return ('vertimus_by_ids', [self.branch.id, self.domain.id, self.language.id])

    def change_state(self, state_class):
        self.name = state_class.name
        self.__class__ = state_class
        self.save()

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
            action.apply(self, person, comment, file)
            if not isinstance(self, StateNone):
                self.person = person
                self.save()

                if isinstance(self, StateCommitted):
                    # Committed is the last state of the workflow, archive actions
                    self.apply_action(ActionAA(), person)
        else:
            raise Exception('Not allowed')

    def get_action_sequence_from_level(self, level):
        """Get the sequence corresponding to the requested level.
           The first level is 1."""
        assert level > 0, "Level must be greater than 0"

        query = self.actiondbarchived_set.all().values('sequence').distinct().order_by('-sequence')[level-1:level]
        sequence = None
        if len(query) > 0:
            sequence = query[0]['sequence']
        return sequence


class StateNone(State):
    name = 'None'
    description = _('Inactive')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        action_names = []

        if person.is_translator(self.language.team) or person.is_maintainer_of(self.branch.module):
            action_names = ['RT']

        return self._get_available_actions(person, action_names)


class StateTranslating(State):
    name = 'Translating'
    description = _('Translating')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        action_names = []

        if (self.person == person):
            action_names = ['UT', 'UNDO']

        return self._get_available_actions(person, action_names)


class StateTranslated(State):
    name = 'Translated'
    description = _('Translated')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        action_names = []

        if person.is_reviewer(self.language.team):
            action_names.append('RP')

        if person.is_translator(self.language.team):
            action_names.append('RT')
            action_names.append('TR')

        if person.is_committer(self.language.team):
            action_names.append('TC')

        return self._get_available_actions(person, action_names)


class StateProofreading(State):
    name = 'Proofreading'
    description = _('Proofreading')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        action_names = []

        if person.is_reviewer(self.language.team):
            if (self.person == person):
                action_names = ['UP', 'TR', 'TC', 'UNDO']

        return self._get_available_actions(person, action_names)


class StateProofread(State):
    name = 'Proofread'
    # Translators: This is a status, not a verb
    description = _('Proofread')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        if person.is_reviewer(self.language.team):
            action_names = ['TC', 'RP', 'TR']
        else:
            action_names = []
        if not self.branch.is_vcs_readonly() and person.is_committer(self.language.team):
            action_names.insert(1, 'CI')

        return self._get_available_actions(person, action_names)


class StateToReview(State):
    name = 'ToReview'
    description = _('To Review')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        action_names = []
        if person.is_translator(self.language.team):
            action_names.append('RT')

        return self._get_available_actions(person, action_names)


class StateToCommit(State):
    name = 'ToCommit'
    description = _('To Commit')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        if person.is_committer(self.language.team):
            action_names = ['RC', 'TR']
            if not self.branch.is_vcs_readonly():
                action_names.insert(1, 'CI')
        else:
            action_names = []

        return self._get_available_actions(person, action_names)


class StateCommitting(State):
    name = 'Committing'
    description = _('Committing')

    class Meta:
        proxy = True

    def get_available_actions(self, person):
        action_names = []

        if person.is_committer(self.language.team):
            if (self.person == person):
                action_names = ['IC', 'TR', 'UNDO']

        return self._get_available_actions(person, action_names)


class StateCommitted(State):
    name = 'Committed'
    description = _('Committed')

    class Meta:
        proxy = True

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
    state_db = models.ForeignKey(State)
    person = models.ForeignKey(Person)

    name = models.SlugField(max_length=8)
    description = None
    created = models.DateTimeField(auto_now_add=True, editable=False)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=generate_upload_filename, blank=True, null=True)
    #up_file     = models.OneToOneField(PoFile, null=True, related_name='action_p')
    #merged_file = models.OneToOneField(PoFile, null=True, related_name='action_m')

    class Meta:
        db_table = 'action'
        verbose_name = 'action'

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
            merged_path = "%s.merged.po" % self.file.path[:-3]
            command = "msgmerge --previous -o %(out_po)s %(po_file)s %(pot_file)s" % {
                'out_po':   merged_path,
                'po_file':  self.file.path,
                'pot_file': pot_file
            }
            run_shell_command(command)
            # If uploaded file is reduced, run po_grep *after* merge
            if is_po_reduced(self.file):
                temp_path = "%s.temp.po" % self.file.path[:-3]
                shutil.copy(merged_path, temp_path)
                po_grep(temp_path, merged_path, self.state_db.domain.red_filter)
                os.remove(temp_path)

    @classmethod
    def get_action_history(cls, state_db):
        return action_db_get_action_history(cls, state_db=state_db)

def generate_archive_filename(instance, original_filename):
    return "%s/%s" % (settings.UPLOAD_ARCHIVED_DIR, os.path.basename(original_filename))

class ActionDbArchived(models.Model):
    state_db = models.ForeignKey(State)
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

    @classmethod
    def clean_old_actions(cls, days):
        """ Delete old archived actions after some (now-days) time """
        # In each sequence, test date of the latest action, to delete whole sequences instead of individual actions
        for action in ActionDbArchived.objects.values('sequence'
            ).annotate(max_created=Max('created')
            ).filter(max_created__lt=datetime.now()-timedelta(days=days)):
            # Call each action delete() so as file is also deleted
            for act in ActionDbArchived.objects.filter(sequence=action['sequence']):
                act.delete()

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
        self._action_db = ActionDb(state_db=state, person=person,
            name=self.name, comment=comment, file=file)
        if file:
            self._action_db.file.save(file.name, file, save=False)
        self._action_db.save()

        # Reactivating the role if needed
        try:
            role = person.role_set.get(team=state.language.team)
            if not role.is_active:
                role.is_active = True
                role.save()
        except Role.DoesNotExist:
            pass

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

    def send_mail_new_state(self, state, recipient_list):
        # Remove None and empty string items from the list
        recipient_list = filter(lambda x: x and x is not None, recipient_list)

        if recipient_list:
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

The new state of %(module)s - %(branch)s - %(domain)s (%(language)s) is now '%(new_state)s'.
%(url)s

""") % {
                'module': state.branch.module.name,
                'branch': state.branch.name,
                'domain': state.domain.name,
                'language': state.language.get_name(),
                'new_state': state,
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

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        # Send an email to all translators of the page
        translator_emails = set()
        for d in Person.objects.filter(actiondb__state_db=state).values('email'):
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

class ActionRT(ActionAbstract):
    name = 'RT'
    description = _('Reserve for translation')
    target_state = StateTranslating
    file_is_prohibited = True

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        state.change_state(self.target_state)

class ActionUT(ActionAbstract):
    name = 'UT'
    description = _('Upload the new translation')
    target_state = StateTranslated
    file_is_required = True

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        state.change_state(self.target_state)
        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionRP(ActionAbstract):
    name = 'RP'
    description = _('Reserve for proofreading')
    target_state = StateProofreading
    file_is_prohibited = True

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        state.change_state(self.target_state)

class ActionUP(ActionAbstract):
    name = 'UP'
    description = _('Upload the proofread translation')
    target_state = StateProofread
    file_is_required = True

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        state.change_state(self.target_state)
        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionTC(ActionAbstract):
    name = 'TC'
    # Translators: this means the file is ready to be committed in repository
    description = _('Ready for submission')
    target_state = StateToCommit

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        state.change_state(self.target_state)
        # Send an email to all committers of the team
        committers = [c.email for c in state.language.team.get_committers()]
        self.send_mail_new_state(state, committers)

class ActionCI(ActionAbstract):
    name = 'CI'
    description = _('Submit to repository')
    target_state = StateCommitted
    file_is_prohibited = True

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        action_with_po = self.get_previous_action_with_po()
        try:
            state.branch.commit_po(action_with_po.file.path, state.domain, state.language, person)
            state.change_state(self.target_state)
        except:
            # Commit failed, state unchanged
            self._action_db.delete()
            # FIXME: somewhere the error should be catched and handled properly
            raise Exception(_("The commit failed. The error was: '%s'") % sys.exc_info()[1])

        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionRC(ActionAbstract):
    name = 'RC'
    # Translators: this indicates a committer is going to commit the file in the repository
    description = _('Reserve to submit')
    target_state = StateCommitting
    file_is_prohibited = True

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)
        state.change_state(self.target_state)

class ActionIC(ActionAbstract):
    name = 'IC'
    # Translators: this is used to indicate the file has been committed in the repository
    description = _('Inform of submission')
    target_state = StateCommitted

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        state.change_state(self.target_state)
        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionTR(ActionAbstract):
    name = 'TR'
    # Translators: regardless of the translation completion, this file need to be reviewed
    description = _('Review required')
    target_state = StateToReview
    arg_is_required = True

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        state.change_state(self.target_state)
        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionAA(ActionAbstract):
    name = 'AA'
    description = _('Archive the actions')
    target_state = StateNone

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        actions_db = ActionDb.objects.filter(state_db=state).order_by('id').all()

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
        state.change_state(self.target_state)

class ActionUNDO(ActionAbstract):
    name = 'UNDO'
    description = _('Undo the last state change')

    def apply(self, state, person, comment=None, file=None):
        self.save_action_db(state, person, comment, file)

        # Exclude WC because this action is a noop on State
        actions_db = ActionDb.objects.filter(state_db__id=state.id).exclude(name='WC').order_by('-id')
        i = 0
        while (i < len(actions_db)):
            if actions_db[i].name == 'UNDO':
                # Skip Undo and the associated action
                i = i + 2
            else:
                # Found
                action = actions_db[i].get_action()
                state.change_state(action.target_state)
                return
        state.change_state(StateNone)

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

def delete_action_files(sender, instance, **kwargs):
    """
    post_delete callback for ActionDb that deletes the file + the merged file from upload
    directory.
    """
    if instance.file:
        if instance.file.path.endswith('.po'):
            merged_file = instance.file.path[:-3] + ".merged.po"
            if os.access(merged_file, os.W_OK):
                 os.remove(merged_file)
        if os.access(instance.file.path, os.W_OK):
             os.remove(instance.file.path)
post_delete.connect(delete_action_files, sender=ActionDb)
post_delete.connect(delete_action_files, sender=ActionDbArchived)

""" The following string is just reproduced from a template so as a translator comment
    can be added (comments are not supported in templates) """
# Translators: human_level is an ordinal expression ('1st',' 2nd',...)
# which should be localized in Django itself
dummy = ugettext("Archived Actions (%(human_level)s archived series)" % {'human_level':0})
