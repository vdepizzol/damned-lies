from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from people.models import Person

class PersonAdmin(admin.ModelAdmin):
    search_fields = ('username', 'first_name', 'last_name')
    list_display = ('username', 'first_name', 'last_name', 'email')

UserAdmin.list_display = ('username', 'email', 'last_name', 'first_name', 'is_active', 'last_login')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Person, PersonAdmin)
