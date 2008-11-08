from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'languages.views.languages', name='languages'),
    url(r'(?P<locale>[\w\-@]+)/(?P<release_name>[\w-]+)/$', 'languages.views.language_release', name='language_release'),
    url(r'(?P<team_slug>[\w\-@]+)/$', 'teams.views.team', name='team_slug'),
)
