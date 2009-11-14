from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(
        regex = r'^$',
        view = 'languages.views.languages',
        name = 'languages'),
    url(
        regex = r'^(?P<locale>[\w\-@]+)/all/(?P<dtype>(ui|doc)+)/$',
        view = 'languages.views.language_all',
        name = 'language_all'),
    url(
        regex = r'^(?P<locale>[\w\-@]+)/rel-archives/$',
        view = 'languages.views.release_archives',
        name = 'language_release_archives'),
    url(
        regex = r'^(?P<locale>[\w\-@]+)/(?P<release_name>[\w-]+)/(?P<dtype>(ui|doc)+)/$',
        view = 'languages.views.language_release',
        name = 'language_release'),
    url(
        regex = r'^(?P<locale>[\w\-@]+)/(?P<release_name>[\w-]+).xml$',
        view = 'languages.views.language_release_xml'),
    url(
        regex = r'^(?P<locale>[\w\-@]+)/(?P<release_name>[\w-]+)/(?P<dtype>(ui|doc)+).tar.gz$',
        view = 'languages.views.language_release_tar'),
    url(
        regex = r'^(?P<team_slug>[\w\-@]+)/$',
        view = 'teams.views.team'),
)
