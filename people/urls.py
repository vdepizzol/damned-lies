from django.conf.urls.defaults import *

from people.views import PeopleListView


# Regex order is really important here
urlpatterns = patterns('people.views',
    url(
        regex = r'^detail_change/$',
        view = 'person_detail_change',
        name='person_detail_change'),
    url(
        regex = r'^password_change/$',
        view = 'person_password_change',
        name='person_password_change'),
    url(
        regex = r'^team_join/$',
        view = 'person_team_join',
        name='person_team_join'),
    url(
        regex = r'^team_leave/(?P<team_slug>[\w\-@]+)/$',
        view = 'person_team_leave',
        name='person_team_leave'),
    url(
        regex = r'^(?P<person_id>\d+)/$',
        view = 'person_detail',
        name='person_detail_id'),
    # Equivalent to the previous, but using username instead of user pk
    url(
        regex = r'^(?P<person_username>[\w@\.\-]+)/$',
        view = 'person_detail',
        name='person_detail_username'),
)

urlpatterns += patterns('',
    url(r'^$', PeopleListView.as_view(), name='people'),
)
