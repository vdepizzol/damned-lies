from django.conf.urls.defaults import *

urlpatterns = patterns('vertimus.views',
    url(r'^(?P<stats_id>\d+)/(?P<lang_id>\d+)$', 'vertimus_by_stats_id', name='vertimus-stats-id-view'),
    url(r'^(?P<branch_id>\d+)/(?P<domain_id>\d+)/(?P<language_id>\d+)', 'vertimus_by_ids', name='vertimus-ids-view'),
    url(r'^(?P<module_name>[\w\+\-\.]+)/(?P<branch_name>[\w\-\.]+)/(?P<domain_name>[\w\-]+)/(?P<locale_name>[\w\-@]+)', 'vertimus_by_names', name='vertimus-names-view'),
    url(r'^diff/(?P<action_id>\d+)$', 'vertimus_diff', name='vertimus-diff-view')
)
