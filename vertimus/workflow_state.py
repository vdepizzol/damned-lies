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

class WorkflowState(object):
    """Abstract class"""
    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.color = ''

    def common_get_actions(self, action_codes=[]):
        action_codes.append('WC')
        return [ eval('WorkflowAction' + action_code)() for action_code in action_codes]

    def __unicode__(self):
        return self.name

    def get_code(self):
        return self.code

class WorkflowStateNone(WorkflowState):
    def __init__(self):
        super(WorkflowStateNone, self).__init__('None', 'Inactive')

    def get_actions(self, module, user):
        return self.common_get_actions(['RT'])


class WorkflowStateCommitted(WorkflowState):
    def __init__(self):
        super(WorkflowStateCommitted, self).__init__('Committed', 'Committed')

    def get_actions(self, module, user):
        return self.common_get_actions()


class WorkflowStateCommitting(WorkflowState):
    def __init__(self):
        super(WorkflowStateCommitting, self).__init__('Committing', 'Committing')
        
    def get_actions(self, module, user):
        action_codes = []

        if user.is_commiter:
            # FIXME Not imple
            last_user = module.get_last_user()
            # if (type(last_user) is User):
            if (True):
                if (user.id == last_user.id):
                    action_codes = ['IC', 'TR', 'TC', 'UNDO']
            
        return self.common_get_actions(action_codes)


class WorkflowStateProofread(WorkflowState):
    def __init__(self):
        super(WorkflowStateProofread, self).__init__('Proofread', 'Proofread')

    def get_actions(self, module, user):
        if user.is_reviewer:
            action_codes = ['TC', 'TR']
        else:
            action_codes = []


class WorkflowStateProofreading(WorkflowState):
    def __init__(self):
        super(WorkflowStateProofreading, self).__init__('Proofreading', 'Proofreading')

    def get_actions(self, module, user):
        action_codes = []
        
        if user.is_commiter:
            # FIXME Not implemented
            last_user = module.get_last_user()
            if type(last_user) is User:
                if user.id == last_user.id:
                    action_codes = ['UP', 'TR', 'TC', 'UNDO']
                    
        return self.common_get_actions(action_codes)


class WorkflowStateToCommit(WorkflowState):
    def __init__(self):
        super(WorkflowStateToCommit, self).__init__('ToCommit', 'To Commit')

    def get_actions(self, module, user):
        if user.is_commiter:
            action_codes = ['RC', 'TR']
        else:
            action_codes = []
            
        return self.common_get_actions(action_codes)


class WorkflowStateToReview(WorkflowState):
    def __init__(self):
        super(WorkflowStateToReview, self).__init__('ToReview', 'To Review')
        self.color = 'needswork';

    def get_actions(self, module, user):
        return self.common_get_actions(['RT'])


class WorkflowStateTranslated(WorkflowState):
    def __init__(self):
        super(WorkflowStateTranslated, self).__init__('Translated', 'Translated')

    def get_actions(self, module, user):
        if user.is_reviewer:
            action_codes = ['RP']
        else:
            action_codes = []

        action_codes.append('RT')
        return self.common_get_actions(action_codes)


class WorkflowStateTranslating(WorkflowState):
    def __init__(self):
        super(WorkflowStateTranslating, self).__init__('Translating', 'Translating')

    def get_actions(self, module, user):
        action_codes = []
        last_user = module.get_last_user()
        if type(last_user) is User:
            if user.id == last_user.id:
                action_codes = ['UT', 'UNDO']
                    
        return self.common_get_actions(action_codes)

