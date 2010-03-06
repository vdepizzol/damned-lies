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
from vertimus.models import ActionAbstract
from stats.utils import po_file_stats

class ActionWidget(forms.Select):
    """ Custom widget to disable the separator option (containing "--------") """
    def render_options(self, choices, selected_choices):
        options = super(ActionWidget, self).render_options(choices, selected_choices)
        options = options.replace("<option value=\"None\">--------</option>",
                                  "<option disabled='disabled'>--------</option>")
        return options

class ActionForm(forms.Form):
    action = forms.ChoiceField(label=_("Action"),
#        help_text="Choose an action you want to apply",
        choices=(),
        widget=ActionWidget)
    comment = forms.CharField(label=_("Comment"),
#        help_text="Leave a comment to explain your action",
        max_length=5000,
        required=False,
        widget=forms.Textarea(attrs={'rows':8, 'cols':70}))
    file = forms.FileField(label=_("File"), required=False,
                           help_text=_("Upload a .po, .gz, .bz2 or .png file"))

    def __init__(self, available_actions, *args, **kwargs):
        super(ActionForm, self).__init__(*args, **kwargs)
        self.fields['action'].choices = available_actions

    def clean_file(self):
        data = self.cleaned_data['file']
        if data:
            ext = os.path.splitext(data.name)[1]
            if ext not in ('.po', '.gz', '.bz2', '.png'):
                raise forms.ValidationError(_("Only files with extension .po, .gz, .bz2 or .png are admitted."))
            # If this is a .po file, check validity (msgfmt)
            if ext == '.po':
                res = po_file_stats(data)
                if res['errors']:
                    raise forms.ValidationError(_(".po file does not pass 'msgfmt -vc'. Please correct the file and try again."))
        return data

    def clean(self):
        cleaned_data = self.cleaned_data
        action_code = cleaned_data.get('action')
        if action_code is None:
            raise forms.ValidationError(_("Invalid action. Someone probably posted another action just before you."))
        action = ActionAbstract.new_by_name(action_code)
        comment = cleaned_data.get('comment')
        file = cleaned_data.get('file')

        if action.comment_is_required and not comment:
            raise forms.ValidationError(_("A comment is needed for this action."))

        if action.arg_is_required and not comment and not file:
            raise forms.ValidationError(_("A comment or a file is needed for this action."))

        if action.file_is_required and not file:
            raise forms.ValidationError(_("A file is needed for this action."))

        if action.file_is_prohibited and file:
            raise forms.ValidationError(_("Please, don't send a file with a 'Reserve' action."))

        return cleaned_data
