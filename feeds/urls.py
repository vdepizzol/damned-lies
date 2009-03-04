from django.conf.urls.defaults import *
from vertimus.feeds import LatestActionsByLanguage, LatestActionsByTeam

feeds = {
    'languages': LatestActionsByLanguage,
    'teams': LatestActionsByTeam,
}

urlpatterns = patterns('',
    (r'^(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}),
)
