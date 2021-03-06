# Django settings for djamnedlies project.

import os
from django.conf import global_settings
gettext_noop = lambda s: s

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_SERVE = True
USE_DEBUG_TOOLBAR = False
USE_DJANGO_OPENID = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = PROJECT_PATH.split('/')[-1]

ADMINS = (
    ('Your Name', 'your_address@example.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME'  : os.path.join(PROJECT_PATH, 'database.db'),
    }
}
# Please refer to the README file to create an UTF-8 database with MySQL.

EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_SUBJECT_PREFIX = '[Damned Lies]'
DEFAULT_FROM_EMAIL = 'gnomeweb@gnome.org'
SERVER_EMAIL = 'gnomeweb@gnome.org'
# When in STRINGFREEZE, where to send notifications (gnome-i18n@gnome.org) on any POT changes
NOTIFICATIONS_TO = ['gnome-i18n@gnome.org']
ENTER_BUG_URL = 'http://bugzilla.gnome.org/enter_bug.cgi?product=damned-lies&component=l10n.gnome.org'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Zurich'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'
LANGUAGES = list(global_settings.LANGUAGES) + [
    # Add here languages with translations for D-L but not for Django
    ('eo', gettext_noop('Esperanto')),
    ('ku', gettext_noop('Kurdish')),
]

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = (
    os.path.join(PROJECT_PATH, 'locale'),
)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Local directory path for VCS checkout
SCRATCHDIR = ""
POTDIR = os.path.join(SCRATCHDIR, "POT")

# The regex is used to determine if the module is in the standard VCS of the project
VCS_HOME_REGEX = "git\.gnome\.org"
VCS_HOME_WARNING = gettext_noop(u"This module is not part of the GNOME Git repository. Please check the module's web page to see where to send translations.")

# By default, Django stores files locally, using the MEDIA_ROOT and MEDIA_URL settings
UPLOAD_DIR = 'upload'
UPLOAD_ARCHIVED_DIR = 'upload-archived'
FILE_UPLOAD_PERMISSIONS = 0600


# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

LOGIN_URL = '/login/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'zk!^92901p458c8lo0(fox-&k7jj(aple76_k%eva7b1)xjo8-'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Default:
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    # Custom:
    "common.context_processors.utils",
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = '%s.urls' % PROJECT_NAME

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.markup',
    'django.contrib.messages',
    'south',
    'common',
    'languages',
    'people',
    'stats',
    'teams',
    'vertimus',
    'feeds',
)

INTERNAL_IPS=('127.0.0.1',)

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'
LOGIN_REDIRECT_URL = '/'

# Members of this group can edit all team's details and change team coordinatorship
ADMIN_GROUP = ''

try:
    from local_settings import *
except ImportError:
    pass

if USE_DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar',)

if USE_DJANGO_OPENID:
    INSTALLED_APPS += ('django_openid_auth',)
    AUTHENTICATION_BACKENDS = (
        'django_openid_auth.auth.OpenIDBackend',
        'django.contrib.auth.backends.ModelBackend',
    )
    OPENID_CREATE_USERS = False
    OPENID_UPDATE_DETAILS_FROM_SREG = True
    OPENID_UPDATE_DETAILS_FROM_AX = True

