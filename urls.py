from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'common.views.index', name='home'),
    url(r'^login/$', 'common.views.site_login', name='login'),
    url(r'^register/$', 'common.views.site_register', name='register'),
    url(r'^register/success$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/register_success.html'}, name='register_success'),
    url(r'^register/activate/(?P<key>\w+)$', 'common.views.activate_account', name='register_activation'),
    (r'^password_reset/$', 'django.contrib.auth.views.password_reset', {'template_name':'registration/password_reset_form.html'}),
    (r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done', {'template_name':'registration/password_reset_done.html'}),
    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),
    (r'^teams/', include('teams.urls')),
    (r'^people/', include('people.urls')),
    # users is the hardcoded url in the contrib.auth User class, making it identical to /people
    (r'^users/', include('people.urls')),
    (r'^languages/', include('languages.urls')),
    (r'^vertimus/', include('vertimus.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^admin/(.*)', admin.site.root),
    (r'^rss/', include('feeds.urls')),
)

urlpatterns += patterns('stats.views',
    url(r'^module/$', 'modules', name='modules'),
    (r'^module/(?P<module_name>[\w\-\+]+)/$', 'module'),
    (r'^module/(?P<module_name>[\w\-\+]+)/edit/branches/$', 'module_edit_branches'),
    (r'^module/(?P<module_name>[\w\-\+]+)/branch/(?P<branch_name>[\w-]+)/$', 'module_branch'),
    (r'^module/(?P<module_name>[\w\-\+]+)/(?P<potbase>[\w-]+)/(?P<branch_name>[\w-]+)/(?P<langcode>[\w@]+)/images/$', 'docimages'),
    url(r'^releases/(?P<format>(html|json|xml))?/?$', 'releases', name='releases'),
    (r'^releases/(?P<release_name>[\w-]+)/(?P<format>(html|xml))?/?$', 'release'),
    (r'^releases/compare/(?P<dtype>\w+)/(?P<rels_to_compare>[\w-]+)/$', 'compare_by_releases'),
)

if 'django_openid' in settings.INSTALLED_APPS:
    from django_openid.auth import AuthConsumer
    
    urlpatterns += patterns('',
        # ...
        (r'^openid/(.*)', AuthConsumer()),
    )

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
        (r'^POT/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.POTDIR}),
        (r'^(robots.txt)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
