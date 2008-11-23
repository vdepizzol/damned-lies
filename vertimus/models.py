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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from stats.models import Branch, Domain
from languages.models import Language
from people.models import Person

ACTION_CODES = (
    'WC', 
    'RT', 'UT',
    'RP', 'UP',
    'TC', 'RC',
    'IC', 'TR',
    'BA', 'UNDO')

class VtmAction(models.Model):
    branch = models.ForeignKey(Branch)
    domain = models.ForeignKey(Domain)
    language = models.ForeignKey(Language)
    person = models.ForeignKey(Person)

    code = models.CharField(max_length=8)
    created = models.DateField(auto_now_add=True, editable=False)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='vertimus/%Y/%m/', blank=True, null=True)

    class Meta:
        db_table = 'vtm_action'
        ordering = ('created',)
        get_latest_by = 'created'

    @classmethod
    def get_all(cls):
        actions = []
        for code in ACTION_CODES:
            actions.append(eval('VtmAction' + code + '()'))
    
    @classmethod
    def get_last_action(cls, branch, domain, language):
        return VtmAction.objects.filter(
            branch=branch, domain=domain, language=language).order_by('-created')[0]

    def apply(self, branch, domain, language, person, comment=None, file=None):
        self.branch = branch
        self.domain = domain
        self.language = language
        self.person = person
        self.comment = comment
        self.file = file
        self.save()

        return self._apply_child()

    def __unicode__(self):
        return self.name

#
# States
#

class VtmState(object):
    """Abstract class"""
    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.color = ''

    def __unicode__(self):
        return self.name

    def get_code(self):
        return self.code

    @classmethod
    def get_actions(cls, action_codes=[]):
        action_codes.append('WC')
        return [ eval('VtmAction' + action_code)() for action_code in action_codes ]

    def apply_action(self, action, branch, domain, language, person, comment=None, file=None):
        new_state = action.apply(branch, domain, language, person, comment, file)
        if new_state == None:
            return self
        else:
            return new_state

    def apply_action_code(self, action_code, branch, domain, language, person, comment=None, file=None):
        action = eval('VtmAction' + action_code)()
        self.apply_action(action, branch, domain, language, person, comment, file)


class VtmStateNone(VtmState):
    def __init__(self):
        super(VtmStateNone, self).__init__('None', 'Inactive')

    def get_actions(self, branch, domain, language, person):
        return super(VtmStateNone, self).get_actions(['RT'])


class VtmStateTranslating(VtmState):
    def __init__(self):
        super(VtmStateTranslating, self).__init__('Translating', 'Translating')

    def get_actions(self, branch, domain, language, person):
        action_codes = []

        last_action = VtmAction.get_last_action(branch, domain, language)
        if (last_action.person == person):
            action_codes = ['UT', 'UNDO']
                    
        return super(VtmStateTranslating, self).get_actions(action_codes)


class VtmStateTranslated(VtmState):
    def __init__(self):
        super(VtmStateTranslated, self).__init__('Translated', 'Translated')

    def get_actions(self, branch, domain, language, person):
        # FIXME
        if person.is_reviewer:
            action_codes = ['RP']
        else:
            action_codes = []

        action_codes.append('RT')
        return super(VtmStateTranslated, self).get_actions(action_codes)


class VtmStateToReview(VtmState):
    def __init__(self):
        super(VtmStateToReview, self).__init__('ToReview', 'To Review')
        self.color = 'needswork';

    def get_actions(self, branch, domain, language, person):
        return super(VtmStateToReview, self).get_actions(['RT'])


class VtmStateProofreading(VtmState):
    def __init__(self):
        super(VtmStateProofreading, self).__init__('Proofreading', 'Proofreading')

    def get_actions(self, branch, domain, language, person):
        action_codes = []
        
        # FIXME
        if person.is_commiter:
            last_action = VtmAction.get_last_action(branch, domain, language)
            if last_action.person == person:
                action_codes = ['UP', 'TR', 'TC', 'UNDO']
                    
        return super(VtmStateProofreading, self).get_actions(action_codes)


class VtmStateProofread(VtmState):
    def __init__(self):
        super(VtmStateProofread, self).__init__('Proofread', 'Proofread')

    def get_actions(self, branch, domain, language, person):
        if person.is_reviewer:
            action_codes = ['TC', 'TR']
        else:
            action_codes = []

        return super(VtmStateProofread, self).get_actions(action_codes)


class VtmStateToCommit(VtmState):
    def __init__(self):
        super(VtmStateToCommit, self).__init__('ToCommit', 'To Commit')

    def get_actions(self, branch, domain, language, person):
        if person.is_commiter:
            action_codes = ['RC', 'TR']
        else:
            action_codes = []
            
        return super(VtmStateToCommit, self).get_actions(action_codes)


class VtmStateCommitting(VtmState):
    def __init__(self):
        super(VtmStateCommitting, self).__init__('Committing', 'Committing')
        
    def get_actions(self, branch, domain, language, person):
        action_codes = []

        # FIXME
        if person.is_commiter:
            last_action = VtmAction.get_last_action(branch, domain, language)
            if (last_action.person == person):
                action_codes = ['IC', 'TR', 'TC', 'UNDO']
            
        return super(VtmStateCommitting, self).get_actions(action_codes)


class VtmStateCommitted(VtmState):
    def __init__(self):
        super(VtmStateCommitted, self).__init__('Committed', 'Committed')

    def get_actions(self, branch, domain, language, person):
        return super(VtmStateCommitted, self).get_actions()

#
# Actions 
#

class VtmActionWC(VtmAction):
    class Meta:
        db_table = 'vtm_action_wc'

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.code = 'WC'
        self.name = 'Write a comment'
        
    def _new_state(self):
        return None

    def _apply_child(self):
        return self._new_state()


class VtmActionRT(VtmAction):
    class Meta:
        db_table = 'vtm_action_rt'

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.code = 'RT'
        self.name = 'Reserve for translation'
        
    def _new_state(self):
        return VtmStateTranslating()

    def _apply_child(self):
        return self._new_state()


class VtmActionUT(VtmAction):
    class Meta:
        db_table = 'vtm_action_ut'

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.code = 'UT'
        self.name = 'Upload the new translation'
        
    def _new_state(self):
        return VtmStateTranslated()

    def _apply_child(self):
        return self._new_state()


class VtmActionRP(VtmAction):
    class Meta:
        db_table = 'vtm_action_rp'
        
    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.code = 'RP'
        self.name = 'Reserve for proofreading'

    def _new_state(self):
        return VtmStateProofreading()

    def _apply_child(self, branch, domain, language, person):
        return self._new_state()

    
