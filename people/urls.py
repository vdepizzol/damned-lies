from django.conf.urls.defaults import *
from people.models import Person

info_dict = {
    'queryset': Person.objects.all(),
    'template_object_name': 'person',
    'extra_context': { 
        'pageSection': "teams"
    }
}

urlpatterns = patterns('django.views.generic.list_detail',
    url(r'^$', 'object_list', dict(info_dict), 'persons'),                    
    url(r'(?P<object_id>\d+)/$', 'object_detail', dict(info_dict), 'person')
)
