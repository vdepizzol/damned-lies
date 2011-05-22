# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2009 Stéphane Raimbault <stephane.raimbault@gmail.com>
# Copyright (c) 2011 Claude Paroz <claude@2xlibre.net>
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

    def change_state(self, state_class, person=None):
        self.name = state_class.name
        self.person = person
        self.__class__ = state_class
        self.save()

    def _get_available_actions(self, person, action_names):
        action_names.append('WC')
        if person.is_committer(self.language.team) and 'IC' not in action_names:
            action_names.extend(('Separator', 'IC'))
            if self.name not in ('None', 'Committed'):
                action_names.append('AA')
        return [eval('Action' + action_name)() for action_name in action_names]

    def get_action_sequence_from_level(self, level):
        """Get the sequence corresponding to the requested level.
           The first level is 1."""
        assert level > 0, "Level must be greater than 0"

        query = ActionArchived.objects.filter(state_db=self).values('sequence').distinct().order_by('-sequence')[level-1:level]
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
    ('WC', _('Write a comment')),
    ('RT', _('Reserve for translation')),
    ('UT', _('Upload the new translation')),
    ('RP', _('Reserve for proofreading')),
    ('UP', _('Upload the proofread translation')),
    # Translators: this means the file is ready to be committed in repository
    ('TC', _('Ready for submission')),
    ('CI', _('Submit to repository')),
    # Translators: this indicates a committer is going to commit the file in the repository
    ('RC', _('Reserve to submit')),
    # Translators: this is used to indicate the file has been committed in the repository
    ('IC', _('Inform of submission')),
    # Translators: regardless of the translation completion, this file need to be reviewed
    ('TR', _('Review required')),
    ('AA', _('Archive the actions')),
    ('UNDO', _('Undo the last state change')),
)

def generate_upload_filename(instance, filename):
    if isinstance(instance, ActionArchived):
        return "%s/%s" % (settings.UPLOAD_ARCHIVED_DIR, os.path.basename(filename))
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

class ActionAbstract(models.Model):
    """ Common model for Action and ActionArchived """
    state_db = models.ForeignKey(State)
    person = models.ForeignKey(Person)

    name = models.SlugField(max_length=8)
    created = models.DateTimeField(editable=False)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=generate_upload_filename, blank=True, null=True)
    #up_file     = models.OneToOneField(PoFile, null=True, related_name='action_p')
    #merged_file = models.OneToOneField(PoFile, null=True, related_name='action_m')

    # A comment or a file is required
    arg_is_required = False
    comment_is_required = False
    file_is_required = False
    file_is_prohibited = False

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"%s (%s) - %s" % (self.name, self.description, self.id)

    @property
    def description(self):
        return dict(ACTION_NAMES).get(self.name, None)

    def get_filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        else:
            return None

    def has_po_file(self):
        try:
            return self.file.name[-3:] == ".po"
        except:
            return False

    def merged_file(self):
        """If available, returns the merged file as a dict: {'url':'path':'filename'}"""
        mfile_url = mfile_path = mfile_name = None
        if self.file:
            mfile_url = self.file.url[:-3] + ".merged.po"
            mfile_path = self.file.path[:-3] + ".merged.po"
            mfile_name = os.path.basename(mfile_path)
            if not os.access(mfile_path, os.R_OK):
                mfile_url = mfile_path = mfile_name = None
        return {'url': mfile_url, 'path': mfile_path, 'filename': mfile_name}

    @classmethod
    def get_action_history(cls, state=None, sequence=None):
        """
        Return action history as a list of tuples (action, file_history),
        file_history is a list of previous po files, used in vertimus view to
        generate diff links
        sequence argument is only valid on ActionArchived instances
        """
        history = []
        if state or sequence:
            file_history = [{'action_id':0, 'title': ugettext("File in repository")}]
            if not sequence:
                query = cls.objects.filter(state_db__id=state.id)
            else:
                # Not necessary to filter on state with a sequence (unique)
                query = cls.objects.filter(sequence=sequence)
            for action in query.order_by('id'):
                history.append((action, list(file_history)))
                if action.file and action.file.path.endswith('.po'):
                    file_history.insert(0, {
                        'action_id': action.id,
                        'title': ugettext("Uploaded file by %(name)s on %(date)s") % {
                            'name': action.person.name,
                            'date': action.created },
                        })
        return history


class Action(ActionAbstract):
    class Meta:
        db_table = 'action'
        verbose_name = 'action'

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        if self.name:
            self.__class__ = eval('Action' + self.name)
        else:
            if getattr(self.__class__, 'name'):
                self.name = self.__class__.name

    @classmethod
    def new_by_name(cls, action_name, **kwargs):
         return eval('Action' + action_name)(**kwargs)

    def save(self, *args, **kwargs):
        if not self.id and not self.created:
            self.created = datetime.today()
        super(Action, self).save(*args, **kwargs)

    def apply_on(self, state):
        if not self in state.get_available_actions(self.person):
            raise Exception('Not allowed')
        self.state_db = state
        if self.file:
            self.file.save(self.file.name, self.file, save=False)
        self.save()
        if not isinstance(self, ActionWC):
            # All actions change state except Writing a comment
            self.state_db.change_state(self.target_state, self.person)
            if self.target_state == StateCommitted:
                self.send_mail_new_state(state, (state.language.team.mailing_list,))
                # Committed is the last state of the workflow, archive actions
                arch_action = self.new_by_name('AA', person=self.person)
                arch_action.apply_on(self.state_db)

    def get_previous_action_with_po(self):
        """
        Return the previous Action with an uploaded file related to the
        same state.
        """
        try:
            action = Action.objects.filter(file__endswith=".po", state_db=self.state_db,
                id__lt=self.id).latest('id')
            return action
        except Action.DoesNotExist:
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
                'new_state': state.description,
                'url': url
            }
            message += self.comment or ugettext("Without comment")
            message += "\n\n" + self.person.name
            message += "\n--\n" + _(u"This is an automated message sent from %s.") % current_site.domain
            mail.send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            activate(current_lang)


def generate_archive_filename(instance, original_filename):
    return "%s/%s" % (settings.UPLOAD_ARCHIVED_DIR, os.path.basename(original_filename))

class ActionArchived(ActionAbstract):
    # The first element of each cycle is null at creation time (and defined
    # afterward).
    sequence = models.IntegerField(null=True)

    class Meta:
        db_table = 'action_archived'

    @classmethod
    def clean_old_actions(cls, days):
        """ Delete old archived actions after some (now-days) time """
        # In each sequence, test date of the latest action, to delete whole sequences instead of individual actions
        for action in ActionArchived.objects.values('sequence'
            ).annotate(max_created=Max('created')
            ).filter(max_created__lt=datetime.now()-timedelta(days=days)):
            # Call each action delete() so as file is also deleted
            for act in ActionArchived.objects.filter(sequence=action['sequence']):
                act.delete()


class ActionWC(Action):
    name = 'WC'
    comment_is_required = True

    class Meta:
        proxy = True

    def apply_on(self, state):
        super(ActionWC, self).apply_on(state)

        # Send an email to all translators of the page
        translator_emails = set()
        for d in Person.objects.filter(action__state_db=state).values('email'):
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
            message += self.comment or ugettext("Without comment")
            message += "\n\n" + self.person.name
            message += "\n--\n" + _(u"This is an automated message sent from %s.") % current_site.domain
            mail.send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, translator_emails)
            activate(current_lang)

class ActionRT(Action):
    name = 'RT'
    target_state = StateTranslating
    file_is_prohibited = True

    class Meta:
        proxy = True

class ActionUT(Action):
    name = 'UT'
    target_state = StateTranslated
    file_is_required = True

    class Meta:
        proxy = True

    def apply_on(self, state):
        super(ActionUT, self).apply_on(state)
        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionRP(Action):
    name = 'RP'
    target_state = StateProofreading
    file_is_prohibited = True

    class Meta:
        proxy = True

class ActionUP(Action):
    name = 'UP'
    target_state = StateProofread
    file_is_required = True

    class Meta:
        proxy = True

    def apply_on(self, state):
        super(ActionUP, self).apply_on(state)
        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionTC(Action):
    name = 'TC'
    target_state = StateToCommit

    class Meta:
        proxy = True

    def apply_on(self, state):
        super(ActionTC, self).apply_on(state)
        # Send an email to all committers of the team
        committers = [c.email for c in state.language.team.get_committers()]
        self.send_mail_new_state(state, committers)

class ActionCI(Action):
    name = 'CI'
    target_state = StateCommitted
    file_is_prohibited = True

    class Meta:
        proxy = True

    def apply_on(self, state):
        action_with_po = self.get_previous_action_with_po()
        try:
            state.branch.commit_po(action_with_po.file.path, state.domain, state.language, self.person)
        except:
            # Commit failed, state unchanged
            # FIXME: somewhere the error should be catched and handled properly
            raise Exception(_("The commit failed. The error was: '%s'") % sys.exc_info()[1])

        super(ActionCI, self).apply_on(state) # Mail sent in super

class ActionRC(Action):
    name = 'RC'
    target_state = StateCommitting
    file_is_prohibited = True

    class Meta:
        proxy = True

class ActionIC(Action):
    name = 'IC'
    target_state = StateCommitted

    class Meta:
        proxy = True

class ActionTR(Action):
    name = 'TR'
    target_state = StateToReview
    arg_is_required = True

    class Meta:
        proxy = True

    def apply_on(self, state):
        super(ActionTR, self).apply_on(state)
        self.send_mail_new_state(state, (state.language.team.mailing_list,))

class ActionAA(Action):
    name = 'AA'
    target_state = StateNone

    class Meta:
        proxy = True

    def apply_on(self, state):
        super(ActionAA, self).apply_on(state)
        all_actions = Action.objects.filter(state_db=state).order_by('id').all()

        sequence = None
        for action in all_actions:
            file_to_archive = None
            if action.file:
                try:
                    file_to_archive = action.file.file # get a file object, not a filefield
                except IOError:
                    pass
            action_archived = ActionArchived(
                state_db=action.state_db,
                person=action.person,
                name=action.name,
                created=action.created,
                comment=action.comment,
                file=file_to_archive)
            if file_to_archive:
                action_archived.file.save(action.file.name, file_to_archive, save=False)

            if sequence is None:
                # The ID is available after the save()
                action_archived.save()
                sequence = action_archived.id

            action_archived.sequence = sequence
            action_archived.save()

            action.delete() # The file is also automatically deleted, if it is not referenced elsewhere

class ActionUNDO(Action):
    name = 'UNDO'

    class Meta:
        proxy = True

    def apply_on(self, state):
        self.state_db = state
        self.save()

        # Exclude WC because this action is a noop on State
        actions = Action.objects.filter(state_db__id=state.id).exclude(name='WC').order_by('-id')
        skip_next = False
        for action in actions:
            if skip_next:
                skip_next = False
                continue
            if action.name == 'UNDO':
                # Skip Undo and the associated action
                skip_next = True
                continue
            # Found action to revert
            state.change_state(action.target_state, action.person)
            return
        state.change_state(StateNone)

class ActionSeparator(object):
    """ Fake action to add a separator in action menu """
    name = None
    description = "--------"

#
# Signal actions
#
def update_uploaded_files(sender, **kwargs):
    """Callback to handle pot_file_changed signal"""
    actions = Action.objects.filter(state_db__branch=kwargs['branch'],
                                    state_db__domain=kwargs['domain'],
                                    file__endswith=".po")
    for action in actions:
        action.merge_file_with_pot(kwargs['potfile'])
pot_has_changed.connect(update_uploaded_files)

def merge_uploaded_file(sender, instance, **kwargs):
    """
    post_save callback for Action that automatically merge uploaded file
    with latest pot file.
    """
    if not isinstance(instance, Action):
        return
    if instance.file and instance.file.path.endswith('.po'):
        try:
            stat = Statistics.objects.get(branch=instance.state_db.branch, domain=instance.state_db.domain, language=None)
        except Statistics.DoesNotExist:
            return
        potfile = stat.po_path()
        instance.merge_file_with_pot(potfile)
post_save.connect(merge_uploaded_file)

def delete_action_files(sender, instance, **kwargs):
    """
    post_delete callback for Action that deletes the file + the merged file from upload
    directory.
    """
    if not isinstance(instance, ActionAbstract) or not getattr(instance, 'file'):
        return
    if instance.file.path.endswith('.po'):
        merged_file = instance.file.path[:-3] + ".merged.po"
        if os.access(merged_file, os.W_OK):
             os.remove(merged_file)
    if os.access(instance.file.path, os.W_OK):
         os.remove(instance.file.path)
post_delete.connect(delete_action_files)

def reactivate_role(sender, instance, **kwargs):
    # Reactivating the role if needed
    if not isinstance(instance, Action):
        return
    try:
        role = instance.person.role_set.get(team=instance.state_db.language.team, is_active=False)
        role.is_active = True
        role.save()
    except Role.DoesNotExist:
        pass
post_save.connect(reactivate_role)

""" The following string is just reproduced from a template so as a translator comment
    can be added (comments are not supported in templates) """
# Translators: human_level is an ordinal expression ('1st',' 2nd',...)
# which should be localized in Django itself
dummy = ugettext("Archived Actions (%(human_level)s archived series)" % {'human_level':0})
