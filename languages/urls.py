from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'languages.views.languages', name='languages'),
    url(r'^(?P<locale>[\w\-@]+)/(?P<release_name>[\w-]+)/(?P<dtype>(ui|doc)+)/$', 'languages.views.language_release', name='language_release'),
       (r'^(?P<locale>[\w\-@]+)/(?P<release_name>[\w-]+).xml$', 'languages.views.language_release_xml'),
       (r'^(?P<locale>[\w\-@]+)/(?P<release_name>[\w-]+)/(?P<dtype>(ui|doc)+).tar.gz$', 'languages.views.language_release_tar'),
    url(r'^(?P<team_slug>[\w\-@]+)/$', 'teams.views.team', name='team_slug'),
)
