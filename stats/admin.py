# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2011 Claude Paroz <claude@2xlibre.net>.
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

from django.contrib import admin
from django.contrib.admin import helpers
from django.shortcuts import render
from django.utils.encoding import force_unicode
from django import forms
from stats.models import Statistics, Information, Module, Branch, Domain, Category, Release

class BranchInline(admin.TabularInline):
    model = Branch

class DomainInline(admin.TabularInline):
    model = Domain
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = forms.Textarea(attrs={'rows':'1', 'cols':'20'})
        elif db_field.name in ('name', 'directory'):
            kwargs['widget'] = forms.TextInput(attrs={'size':'20'})
        elif db_field.name == 'red_filter':
            kwargs['widget'] = forms.Textarea(attrs={'rows':'1', 'cols':'40'})
        return super(DomainInline, self).formfield_for_dbfield(db_field, **kwargs)

class ModuleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (('name','description'),
                        'homepage', 'comment',
                       ('bugs_base', 'bugs_product', 'bugs_component'),
                       ('vcs_type', 'vcs_root', 'vcs_web'),
                       'ext_platform', 'maintainers')
        }),
    )
    inlines = [ BranchInline, DomainInline ]
    search_fields = ('name',)

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(ModuleAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'description':
            field.widget.attrs['rows'] = '1'
        elif db_field.name == 'comment':
            field.widget.attrs['rows'] = '4'

        return field

class BranchAdmin(admin.ModelAdmin):
    search_fields = ('name', 'module__name')

class DomainAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'directory', 'pot_method')
    search_fields = ('name', 'module__name','directory', 'pot_method')

class CategoryInline(admin.TabularInline):
    model = Category
    raw_id_fields = ('branch',) # Too costly otherwise
    extra = 1

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name', 'branch__module__name')

class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'weight', 'string_frozen')
    list_editable = ('weight',)
    inlines = [ CategoryInline ]
    actions = ['delete_release']

    def delete_release(self, request, queryset):
        """ Admin action to delete releases *with* branches which are not linked to another release """
        if not self.has_delete_permission(request):
            raise PermissionDenied
        if request.POST.get('post'):
            # Already confirmed
            for obj in queryset:
                self.log_deletion(request, obj, force_unicode(obj))
            n = queryset.count()
            b = 0
            for release in queryset:
                branches = Branch.objects.filter(category__release=release)
                for branch in branches:
                    if branch.releases.count() < 2 and not branch.is_head():
                        branch.delete()
                        b += 1
            queryset.delete()
            self.message_user(request, "Successfully deleted %(countr)d release(s) and %(countb)d branch(es)." % {
                "countr": n, "countb": b,
            })
            # Return None to display the change list page again.
            return None
        context = {
            "title": "Are you sure?",
            "queryset": queryset,
            "app_label": self.model._meta.app_label,
            "model_label": self.model._meta.verbose_name_plural,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        }
        return render(request, 'admin/delete_release_confirmation.html', context)
    delete_release.short_description = "Delete release (and associated branches)"

class InformationInline(admin.TabularInline):
    model = Information
    extra = 0

class StatisticsAdmin(admin.ModelAdmin):
    search_fields = ('language__name', 'branch__module__name')
    raw_id_fields = ('branch', 'domain', 'language', 'full_po', 'part_po')
    inlines = [ InformationInline ]

admin.site.register(Statistics, StatisticsAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Release, ReleaseAdmin)
