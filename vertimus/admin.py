# -*- coding: utf-8 -*-
from django.contrib import admin

from vertimus.models import State, Action

class StateAdmin(admin.ModelAdmin):
    raw_id_fields = ('branch', 'domain', 'person',)
    search_fields = ('branch__module__name',)

class ActionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'state_db')
    raw_id_fields = ('state_db', 'person')
    search_fields = ('comment',)

admin.site.register(State, StateAdmin)
admin.site.register(Action, ActionAdmin)
