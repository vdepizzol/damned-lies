# -*- coding: utf-8 -*-
#
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

from django.contrib import admin
from stats.models import Statistics, Information, Module, Branch, Domain, Category, Release

class BranchInline(admin.TabularInline):
    model = Branch

class DomainInline(admin.TabularInline):
    model = Domain
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(DomainInline, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'description':
            field.widget.attrs['rows'] = '1'
        return field

class ModuleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (('name','description'),
                        'homepage', 'comment',
                       ('bugs_base', 'bugs_product', 'bugs_component'),
                       ('vcs_type', 'vcs_root', 'vcs_web'),
                       'maintainers')
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
    pass

class CategoryInline(admin.TabularInline):
    model = Category
    raw_id_fields = ('branch',) # Too costly otherwise
    extra = 1

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name', 'branch__module__name')

class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'string_frozen')
    inlines = [ CategoryInline ]

class InformationInline(admin.TabularInline):
    model = Information
    extra = 0

class StatisticsAdmin(admin.ModelAdmin):
    search_fields = ('language__name', 'branch__module__name')
    inlines = [ InformationInline ]

admin.site.register(Statistics, StatisticsAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Release, ReleaseAdmin)
