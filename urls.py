from django.conf.urls.defaults import *
from django.conf import settings
from stats.conf import settings as stats_settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'common.views.index', name='home'),
    (r'^teams/', include('teams.urls')),
    (r'^people/', include('people.urls')),
    (r'^languages/', include('languages.urls')),
    #(r'^stats/', include('stats.urls')),
    (r'^admin/(.*)', admin.site.root),
)

urlpatterns += patterns('stats.views',
    url(r'^module/$', 'modules', name='modules'),
    (r'^module/(?P<module_name>[\w\-\+]+)$', 'module'),
    (r'^module/(?P<module_name>[\w\-\+]+)/(?P<potbase>\w+)/(?P<branch_name>[\w-]+)/(?P<langcode>\w+)/images/$', 'docimages'),
    url(r'^releases/$', 'releases', name='releases'),
    (r'^releases/(?P<release_name>[\w-]+)$', 'release'),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
        (r'^POT/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': stats_settings.POTDIR}),
    )
