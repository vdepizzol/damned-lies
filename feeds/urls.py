from django.conf.urls.defaults import *
from vertimus.feeds import LatestActionsByLanguage, LatestActionsByTeam

feeds = {
    'languages': LatestActionsByLanguage,
    'teams': LatestActionsByTeam,
}

urlpatterns = patterns('',
    url(
        regex = r'^(?P<url>.*)/$',
        view = 'django.contrib.syndication.views.feed',
        kwargs = {'feed_dict': feeds})
)
