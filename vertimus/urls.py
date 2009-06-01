from django.conf.urls.defaults import *

urlpatterns = patterns('vertimus.views',
    url(
        regex = r'^(?P<stats_id>\d+)/(?P<lang_id>\d+)$',
        view = 'vertimus_by_stats_id',
        name = 'vertimus_by_stats_id'),
    url(
        regex = r'^(?P<branch_id>\d+)/(?P<domain_id>\d+)/(?P<language_id>\d+)',
        view = 'vertimus_by_ids',
        name = 'vertimus_by_ids'),
    url(
        regex = '^(?P<module_name>[\w\+\-\.]+)/(?P<branch_name>[\w\-\.]+)/(?P<domain_name>[\w\-]+)/(?P<locale_name>[\w\-@]+)/level(?P<level>\d+)/$',
        view = 'vertimus_by_names',
        name = 'vertimus_archives_by_names'),
    url(
        regex = r'^(?P<module_name>[\w\+\-\.]+)/(?P<branch_name>[\w\-\.]+)/(?P<domain_name>[\w\-]+)/(?P<locale_name>[\w\-@]+)',
        view = 'vertimus_by_names',
        name = 'vertimus_by_names'),
    url(
        regex = r'^diff/(?P<action_id_1>\d+)/(?P<action_id_2>\d+)?$',
        view = 'vertimus_diff',
        name = 'vertimus_diff'),
)
