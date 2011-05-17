from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('teams.views',
    url(
        regex = r'^(?P<format>(xml))?/?$',
        view = 'teams',
        name = 'teams'),
    url(
        regex = r'^(?P<team_slug>[\w\-@]+)/$',
        view = 'team',
        name = 'team_slug'),
    url(
        regex = r'^(?P<team_slug>[\w\-@]+)/edit/',
        view = 'team_edit',
        name = 'team_edit'),
)
