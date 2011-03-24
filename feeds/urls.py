from django.conf.urls.defaults import *
from vertimus.feeds import LatestActionsByLanguage, LatestActionsByTeam

urlpatterns = patterns('',
    (r'^languages/(?P<locale>.*)/$', LatestActionsByLanguage()),
    (r'^teams/(?P<team_name>.*)/$', LatestActionsByTeam()),
)
