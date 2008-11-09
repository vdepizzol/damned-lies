from django.contrib import admin
from people.models import Person

class PersonAdmin(admin.ModelAdmin):
    search_fields = ('username', 'first_name', 'last_name')
    list_display = ('username', 'first_name', 'last_name', 'email')

admin.site.register(Person, PersonAdmin)
