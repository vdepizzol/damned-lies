# -*- coding: utf-8 -*-
from django.contrib import admin

from vertimus.models import StateDb, ActionDb

class StateDbAdmin(admin.ModelAdmin):
    raw_id_fields = ('branch', 'domain', 'person',)

class ActionDbAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'state_db')

admin.site.register(StateDb, StateDbAdmin)
admin.site.register(ActionDb, ActionDbAdmin)
