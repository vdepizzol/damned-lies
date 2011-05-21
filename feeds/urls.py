from django.conf.urls.defaults import patterns, url
from vertimus.feeds import LatestActionsByLanguage, LatestActionsByTeam

urlpatterns = patterns('',
    url(r'^languages/(?P<locale>.*)/$', LatestActionsByLanguage(), name='lang_feed'),
    url(r'^teams/(?P<team_name>.*)/$', LatestActionsByTeam(), name='team_feed'),
)
