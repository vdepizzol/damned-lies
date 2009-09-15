from django import forms
from stats.models import CATEGORY_CHOICES, Release

class ReleaseField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['required'] = False
        super(ReleaseField, self).__init__(*args, **kwargs)
        if 'label' in kwargs:
            self.is_branch = True

class ModuleBranchForm(forms.Form):
    def __init__(self, module, *args, **kwargs):
        super(ModuleBranchForm, self).__init__(*args, **kwargs)
        self.branch_fields = []
        default_cat_name = None
        for branch in module.get_branches(reverse=True):
            categs = branch.category_set.order_by('name', 'release__name')
            if len(categs):
                for cat in categs:
                    self.fields[str(cat.id)] = ReleaseField(queryset=Release.objects.all(),
                                                            label=branch.name,
                                                            initial=cat.release.pk)
                    self.fields[str(cat.id)+'_cat'] = forms.ChoiceField(choices=CATEGORY_CHOICES,
                                                                        initial=cat.name)
                    self.branch_fields.append((str(cat.id), str(cat.id)+'_cat'))
                default_cat_name = cat.name
            else:
                # Branch is not linked to any release
                self.fields[branch.name] = ReleaseField(queryset=Release.objects.all(),
                                                        label=branch.name)
                self.fields[branch.name+'_cat'] = forms.ChoiceField(choices=CATEGORY_CHOICES,
                                                                    initial=default_cat_name)
                self.branch_fields.append((branch.name, branch.name+'_cat'))

        self.fields['new_branch'] = forms.CharField(required=False)
        self.fields['new_branch_release'] = ReleaseField(queryset=Release.objects.all())
        self.fields['new_branch_category'] = forms.ChoiceField(choices=CATEGORY_CHOICES,
                                                               initial=default_cat_name)

    def get_branches(self):
        for rel_field, cat_field in self.branch_fields:
            yield (self[rel_field], self[cat_field])
