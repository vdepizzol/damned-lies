# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>
# Copyright (c) 2008 Claude Paroz <claude@2xlibre.net>.
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

from django import forms
from django.utils.translation import ugettext_lazy as _

from stats.utils import po_file_stats

class ActionForm(forms.Form):
    action = forms.ChoiceField(label=_("Action"),
#        help_text="Choose an action you want to apply",
        choices=())
    comment = forms.CharField(label=_("Comment"),
#        help_text="Leave a comment to explain your action",
        max_length=1000,
        required=False,
        widget=forms.Textarea)
    file = forms.FileField(label=_("File"), required=False)

    def __init__(self, available_actions, *args, **kwargs):
        super(ActionForm, self).__init__(*args, **kwargs)
        self.fields['action'].choices = available_actions

    def clean_file(self):
        data = self.cleaned_data['file']
        if data:
            ext = os.path.splitext(data.name)[1]
            # If this is a .po file, check validity (msgfmt)
            if ext == ".po":
                res = po_file_stats(data)
                if res['errors']:
                    raise forms.ValidationError(".po file does not pass 'msgfmt -vc'. Please correct the file and try again.")
        return data
