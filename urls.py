from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()

urlpatterns = patterns('',
    url(
        regex = r'^$',
        view = 'common.views.index',
        name = 'home'),
    url(
        regex = r'^login/$',
        view = 'common.views.site_login',
        name = 'login'),
    url(
        regex = r'^register/$',
        view = 'common.views.site_register',
        name = 'register'),
    url(
        regex = r'^help/(?P<topic>\w+)/$',
        view = 'common.views.help',
        name = 'help'),
    url(
        regex = r'^register/success$',
        view = TemplateView.as_view(template_name="registration/register_success.html"),
        name = 'register_success'),
    url(
        regex = r'^register/activate/(?P<key>\w+)$',
        view = 'common.views.activate_account',
        name = 'register_activation'),
    url(
        regex = r'^password_reset/$',
        view = 'django.contrib.auth.views.password_reset',
        kwargs = {'template_name':'registration/password_reset_form.html'}),
    url(
        regex = r'^password_reset/done/$',
        view = 'django.contrib.auth.views.password_reset_done',
        kwargs = {'template_name':'registration/password_reset_done.html'}),
    url(
        regex = r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        view = 'django.contrib.auth.views.password_reset_confirm'),
    url(
        regex = r'^reset/done/$',
        view = 'django.contrib.auth.views.password_reset_complete'),
    url(r'^teams/', include('teams.urls')),
    url(r'^people/', include('people.urls')),
    url(# users is the hardcoded url in the contrib.auth User class, making it identical to /people
        r'^users/', include('people.urls')),
    url(r'^languages/', include('languages.urls')),
    url(r'^vertimus/', include('vertimus.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rss/', include('feeds.urls')),
)

urlpatterns += patterns('stats.views',
    url(
        regex = r'^module/(?P<format>(html|json|xml))?/?$',
        view = 'modules',
        name = 'modules'),
    url(
        regex = r'^module/po/(?P<module_name>[\w\-\+]+)/(?P<domain>\w+)/(?P<branch_name>[\w\-\.]+)/(?P<filename>.*)$',
        view = 'dynamic_po',
        name = 'dynamic_po'),
    url(
        regex = r'^module/(?P<module_name>[\w\-\+]+)/$',
        view = 'module'),
    url(
        regex = r'^module/(?P<module_name>[\w\-\+]+)/edit/branches/$',
        view = 'module_edit_branches'),
    url(
        regex = r'^module/(?P<module_name>[\w\-\+]+)/branch/(?P<branch_name>[\w\-\.]+)/$',
        view = 'module_branch'),
    url(
        regex = r'^module/(?P<module_name>[\w\-\+]+)/(?P<potbase>[\w~-]+)/(?P<branch_name>[\w\-\.]+)/(?P<langcode>[\w@]+)/images/$',
        view = 'docimages'),
    url(
        regex = r'^releases/(?P<format>(html|json|xml))?/?$',
        view = 'releases',
        name = 'releases'),
    url(
        regex = r'^releases/(?P<release_name>[\w-]+)/(?P<format>(html|xml))?/?$',
        view = 'release'),
    url(
        regex = r'^releases/compare/(?P<dtype>\w+)/(?P<rels_to_compare>[/\w-]+)/$',
        view = 'compare_by_releases'),
)

if 'django_openid_auth' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^openid/', include('django_openid_auth.urls')),
    )

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        url(
            regex = r'^media/(?P<path>.*)$',
            view = 'django.views.static.serve',
            kwargs = {'document_root': settings.MEDIA_ROOT}),
        url(
            regex = r'^POT/(?P<path>.*)$',
            view = 'django.views.static.serve',
            kwargs = {'document_root': settings.POTDIR}),
        url(
            regex = r'^(robots.txt)$',
            view = 'django.views.static.serve',
            kwargs = {'document_root': settings.MEDIA_ROOT})
    )
