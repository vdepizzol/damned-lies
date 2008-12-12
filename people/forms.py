from django import forms
from teams.models import Team

class JoinTeamForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(JoinTeamForm, self).__init__(*args, **kwargs)
        self.fields['teams'] = forms.ModelChoiceField(queryset=Team.objects.all())
