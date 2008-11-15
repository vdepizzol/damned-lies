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
from people.models import Person
from languages.models import Language
from stats.models import Branch, Domain
from workflow_state import *

ACTION_CODES = (
    'WC', 
    'RT', 'UT',
    'RP', 'UP',
    'TC', 'RC',
    'IC', 'TR',
    'BA', 'UNDO')

class WorkflowAction(models.Model):
    """Abstract class"""
    person = models.ForeignKey(Person)
    branch = models.ForeignKey(Branch)
    domain = models.ForeignKey(Domain)
    language = models.ForeignKey(Language)
    code = models.CharField(max_length=8)
    created = models.DateField(auto_now_add=True, editable=False)
    comment = models.TextField(null=True)
    # FIXME filename in child or here

    class Meta:
        abstract = True
        ordering = ('created',)
        get_latest_by = 'created'

    def get_all(self):
        actions = []
        for code in ACTION_CODES:
            actions.append(eval('WorkflowAction' + code + '()'))

    # FIXME Apply parent/child call
    def apply(self, person, branch, domain, language, comment=None):
        self.person = person
        self.branch = branch
        self.domain = domain
        self.language = language
        self.comment = comment
        self.save()

        return self._apply_child()

    def __unicode__(self):
        return self.name


class WorkflowActionWC(WorkflowAction):
    class Meta:
        db_table = 'workflow_action_wc'

    def __init__(self):
        models.Model.__init__(self, *args, **kwargs)
        self.code = 'RT'
        self.name = 'Write a comment'
        
    def _new_state(self):
        return None

    def _apply_child(self):
        return self._new_state()


class WorkflowActionRT(WorkflowAction):
    """
    >>> from people.models import Person
    >>> from teams.models import Team
    >>> from languages.models import Language
    >>> from stats.models import Release, Category, Module, Branch, Domain
    >>> p = Person(name=u'Gérard Martin', email='gm@mail.com')
    >>> p.save()
    >>> r = Release(name='gnome-2-24', string_frozen=True, status='official')
    >>> r.save()
    >>> m = Module(name='gedit', bugs_base='nd', bugs_product='d', bugs_component='d', vcs_type='svn', vcs_root='d', vcs_web='d')
    >>> m.save()
    >>> b = Branch(name='trunk', module=m)
    >>> b.save()
    >>> c = Category(release=r, branch=b, name='desktop')
    >>> c.save()
    >>> d = Domain(module=m, name='ihm', dtype='ui', directory='dir')
    >>> d.save()
    >>> t = Team(name='fr', description='GNOME French Team', coordinator=p)
    >>> t.save()
    >>> l = Language(name='french', locale='fr', team=t)
    >>> l.save()
    >>> ma = WorkflowActionRT()
    >>> ma.name
    'Reserve for translation'
    >>> ms_next = ma.apply(p, b, d, l, 'Hi')
    >>> ms_next.get_code()
    'Translating'
    """
    class Meta:
        db_table = 'workflow_action_rc'

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.code = 'RT'
        self.name = 'Reserve for translation'
        
    def _new_state(self):
        return WorkflowStateTranslating()

    def _apply_child(self):
        return self._new_state()


class WorkflowActionUT(WorkflowAction):
    class Meta:
        db_table = 'workflow_action_ut'

    def __init__(self):
        models.Model.__init__(self, *args, **kwargs)
        self.code = 'UT'
        self.name = 'Upload the new translation'
        
    def _new_state(self):
        return WorkflowStateTranslated()

    def _apply_child(self):
        return self._new_state()
