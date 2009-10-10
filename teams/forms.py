from django import forms
from teams.models import Team, ROLE_CHOICES

class EditTeamDetailsForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('webpage_url', 'mailing_list', 'mailing_list_subscribe')

    def __init__(self, *args, **kwargs):
        super(EditTeamDetailsForm, self).__init__(*args, **kwargs)
        for f in ('webpage_url', 'mailing_list', 'mailing_list_subscribe'):
            self.fields[f].widget.attrs['size'] = 60

class EditMemberRoleForm(forms.Form):

    def __init__(self, roles, *args, **kwargs):
        super(EditMemberRoleForm, self).__init__(*args, **kwargs)
        choices = list(ROLE_CHOICES[:-1]) # exclude last element: coordinator
        choices.append(('remove','Remove From Team'))
        for role in roles:
            self.fields[str(role.pk)] = forms.ChoiceField(
                choices=choices,
                label = "<a href='%s'>%s</a>" % (role.person.get_absolute_url(), role.person.name),
                initial=role.role)
        self.fields['form_type'] = forms.CharField(widget=forms.HiddenInput,
                                                   initial=roles[0].role)

    def get_fields(self):
        for key, field in self.fields.items():
            if key not in ('form_type',):
                yield self[key]
