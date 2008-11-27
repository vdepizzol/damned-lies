from django.conf.urls.defaults import *
from people.models import Person


info_dict_list = {
    'queryset': Person.objects.all(),
    'template_object_name': 'person',
    'extra_context': { 
        'pageSection': "teams"
    }
}

info_dict_detail = dict(
    info_dict_list,
    slug_field = 'username'
)
    
urlpatterns = patterns('django.views.generic.list_detail',
    url(r'^$', 'object_list', dict(info_dict_list), 'persons'),                    
    url(r'(?P<object_id>\d+)/$', 'object_detail', dict(info_dict_detail), 'person'),
    # equivalent to the previous, but using username instead of user pk
    url(r'(?P<slug>\w+)/$', 'object_detail', dict(info_dict_detail), 'person'),
)
