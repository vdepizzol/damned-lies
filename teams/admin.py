from django.contrib import admin
from teams.models import Team, Role
from languages.models import Language

class LanguageInline(admin.TabularInline):
    model = Language
    # Languages are not supposed to be created in this form
    extra = 0

class TeamAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('description', 'use_workflow')
    inlines = [ LanguageInline ]

    def formfield_for_dbfield(self, db_field, **kwargs):
        # Reduced text area for aliases
        field = super(TeamAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'description':
            field.widget.attrs['rows'] = '4'

        return field

class RoleAdmin(admin.ModelAdmin):
    search_fields = ('person__first_name', 'person__last_name', 'team__description', 'role')

admin.site.register(Team, TeamAdmin)
admin.site.register(Role, RoleAdmin)
