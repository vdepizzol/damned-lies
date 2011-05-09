from django import forms
from django.utils.translation import ugettext as _

from common.utils import is_site_admin
from teams.models import Team, Role, ROLE_CHOICES

class EditTeamDetailsForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('webpage_url', 'mailing_list', 'mailing_list_subscribe', 'use_workflow', 'presentation')
        widgets = {
            'webpage_url':  forms.TextInput(attrs={'size': 60}),
            'mailing_list': forms.TextInput(attrs={'size': 60}),
            'mailing_list_subscribe': forms.TextInput(attrs={'size': 60}),
            'presentation': forms.Textarea(attrs={'cols': 60}),
        }

    def __init__(self, user, *args, **kwargs):
        super(EditTeamDetailsForm, self).__init__(*args, **kwargs)
        self.user = user
        if is_site_admin(user):
            # Add coordinatorship dropdown
            all_members = [(r.id, r.person.name) for r in Role.objects.select_related('person').filter(team=self.instance)]
            all_members.insert(0, ('', '-------'))
            try:
                current_coord_pk = Role.objects.filter(team=self.instance, role='coordinator')[0].pk
            except IndexError:
                current_coord_pk = None
            self.fields['coordinatorship'] = forms.ChoiceField(
                label    = _("Coordinator"),
                choices  = all_members,
                required = False,
                initial  = current_coord_pk
            )

    def save(self, *args, **kwargs):
        super(EditTeamDetailsForm, self).save(*args, **kwargs)
        if 'coordinatorship' in self.changed_data and is_site_admin(self.user):
            # Change coordinator
            try:
                # Pass current coordinator as committer
                current_coord = Role.objects.filter(team=self.instance, role='coordinator')[0]
                current_coord.role = 'committer'
                current_coord.save()
            except IndexError:
                pass
            if self.cleaned_data['coordinatorship']:
                new_coord = Role.objects.get(pk=self.cleaned_data['coordinatorship'])
                new_coord.role = 'coordinator'
                new_coord.save()

class EditMemberRoleForm(forms.Form):

    def __init__(self, roles, *args, **kwargs):
        super(EditMemberRoleForm, self).__init__(*args, **kwargs)
        choices = list(filter(lambda x:x[0]!='coordinator', ROLE_CHOICES))
        choices.append(('inactivate', _("Mark as Inactive")))
        choices.append(('remove', _("Remove From Team")))
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
