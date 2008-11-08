from django.contrib import admin
from languages.models import Language

class LanguageAdmin(admin.ModelAdmin):
    search_fields = ('name', 'locale')

admin.site.register(Language, LanguageAdmin)
