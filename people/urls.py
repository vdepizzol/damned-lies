from django.conf.urls.defaults import *
from people.models import Person

info_dict_list = {
    'queryset': Person.objects.all(),
    'template_object_name': 'person',
    'extra_context': { 
        'pageSection': "teams"
    }
}
    
urlpatterns = patterns('',
    url(r'^$', 'django.views.generic.list_detail.object_list', dict(info_dict_list), 'persons'),                    
    url(r'^(?P<object_id>\d+)/$', 'people.views.person_detail_from_id', name='person_from_id'),
    # equivalent to the previous, but using username instead of user pk
    url(r'^(?P<slug>\w+)/$', 'people.views.person_detail_from_username', name='person'),
    url(r'^(?P<slug>\w+)/edit$', 'people.views.person_detail_from_username', {'edit_profile': True}, name='person_edit'),
)
