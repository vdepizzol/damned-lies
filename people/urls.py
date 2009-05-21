from django.conf.urls.defaults import *
from people.models import Person

info_dict_list = {
    'queryset': Person.objects.all(),
    'template_object_name': 'person',
    'extra_context': {
        'pageSection': "teams"
    }
}

# Regex order is really important here

urlpatterns = patterns('people.views',
    url(r'^detail_change/$', 'person_detail_change', name='person-detail-change-view'),
    url(r'^password_change/$', 'person_password_change', name='person-password-change-view'),
    url(r'^team_join/$', 'person_team_join', name='person-team-join-view'),
    url(r'^team_leave/(?P<team_slug>[\w\-@]+)/$', 'person_team_leave', name='person-team-leave-view'),
    url(r'^(?P<person_id>\d+)/$', 'person_detail', name='person-id-view'),
    # equivalent to the previous, but using username instead of user pk
    url(r'^(?P<person_username>[\w@\.\-]+)/$', 'person_detail', name='person-username-view'),
)

urlpatterns += patterns('django.views.generic.list_detail',
    url(r'^$', 'object_list', dict(info_dict_list), name='persons-view'),
)
