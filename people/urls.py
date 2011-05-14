from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from people import views


# Regex order is really important here
urlpatterns = patterns('people.views',
    url(
        r'^detail_change/$',
        login_required(views.PersonEditView.as_view()),
        name = 'person_detail_change'),
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
        r'^(?P<pk>\d+)/$',
        views.PersonDetailView.as_view(),
        name = 'person_detail_id'),
    # Equivalent to the previous, but using username instead of user pk
    url(
        r'^(?P<slug>[\w@\.\-]+)/$',
        views.PersonDetailView.as_view(),
        name = 'person_detail_username'),
)

urlpatterns += patterns('',
    url(r'^$', views.PeopleListView.as_view(), name='people'),
)
