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
    url(
        regex = r'^$',
        view = 'teams.views.teams',
        name = 'teams'),
    url(
        regex = r'(?P<team_slug>[\w\-@]+)',
        view = 'teams.views.team',
        name = 'team_slug'),
    url(
        regex = r'(?P<object_id>\d+)',
        view = 'django.views.generic.list_detail.object_detail',
        kwargs = dict(info_dict),
        name = 'team')
)
