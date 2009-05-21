from django.conf.urls.defaults import *
from teams.models import Team

info_dict = {
    'queryset': Team.objects.all(),
    'template_object_name': 'team',
    'slug_field': 'name',
    'extra_context': {
        'pageSection': "teams"
    }
}

urlpatterns = patterns('',
    url(r'^$', 'teams.views.teams', name='teams'),
    #url(r'(?P<slug>\w+)', 'django.views.generic.list_detail.object_detail', dict(info_dict), 'team_slug'),
    url(r'(?P<team_slug>[\w\-@]+)', 'teams.views.team', name='team_slug'),
    url(r'(?P<object_id>\d+)', 'django.views.generic.list_detail.object_detail', dict(info_dict), 'team'),
)
