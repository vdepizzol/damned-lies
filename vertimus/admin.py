# -*- coding: utf-8 -*-
from django.contrib import admin

from vertimus.models import State, ActionDb

class StateAdmin(admin.ModelAdmin):
    raw_id_fields = ('branch', 'domain', 'person',)

class ActionDbAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'state_db')

admin.site.register(State, StateAdmin)
admin.site.register(ActionDb, ActionDbAdmin)
