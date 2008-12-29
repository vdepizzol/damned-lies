from django import forms
from stats.models import Module, Branch, Category, CATEGORY_CHOICES, Release


class ReleaseField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        super(ReleaseField, self).__init__(*args, **kwargs)
        if 'initial' in kwargs:
            self.is_branch = True

class ModuleBranchForm(forms.Form):
    def __init__(self, module, *args, **kwargs):
        super(ModuleBranchForm, self).__init__(*args, **kwargs)
        self.branch_fields = []
        for branch in module.branch_set.all():
            for cat in branch.category_set.order_by('name', 'release__name'):
                self.fields[str(cat.id)] = ReleaseField(queryset=Release.objects.all(),
                                                        label=branch.name,
                                                        initial=cat.release.pk)
                self.fields[str(cat.id)+'_cat'] = forms.ChoiceField(choices=CATEGORY_CHOICES,
                                                                    initial=cat.name)
                self.fields[str(cat.id)+'_del'] = forms.BooleanField(required=False)
                self.branch_fields.append((str(cat.id), str(cat.id)+'_cat', str(cat.id)+'_del'))
                
        self.fields['new_branch'] = forms.CharField(required=False)
        self.fields['new_branch_release'] = ReleaseField(queryset=Release.objects.all(), required=False)
        self.fields['new_branch_category'] = forms.ChoiceField(choices=CATEGORY_CHOICES)

    def get_branches(self):
        for rel_field, cat_field, del_field in self.branch_fields:
            yield (self[rel_field], self[cat_field], self[del_field])

