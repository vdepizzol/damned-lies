# Django settings for djamnedlies project.

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_SERVE = True
USE_DJANGO_EVOLUTION = False
USE_DEBUG_TOOLBAR = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

ADMINS = (
    ('Claude Paroz', 'claude@2xlibre.net'),
    ('Stephane Raimbault', 'stephane.raimbault@gmail.com'),
)

MANAGERS = ADMINS

SERVER_EMAIL = 'gnomeweb@gnome.org'
EMAIL_SUBJECT_PREFIX = '[Damned Lies] '

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = os.path.join(PROJECT_PATH,'database.db')            # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# If you can't use PostgreSQL :-/, here is the MySQL configuration:
#
# DATABASE_HOST = '/var/run/mysqld/mysqld.sock'
#
# DATABASE_OPTIONS = {
#    'read_default_file': '/etc/mysql/my.cnf',
#    'init_command': 'SET storage_engine=INNODB'
# }
# 
# Please refer to the README file to create an UTF-8 database with MySQL.

EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_SUBJECT_PREFIX = '[DL]'
SERVER_EMAIL = 'server@l10n.gnome.org'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Zurich'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# By default, Django stores files locally, using the MEDIA_ROOT and MEDIA_URL settings
UPLOAD_DIR = 'upload'
UPLOAD_BACKUP_DIR = 'upload-backup'
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
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'djamnedlies.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
#    'django_openid',
    'common',
    'languages',
    'people',
    'stats',
    'teams',
    'vertimus'
)

INTERNAL_IPS=('127.0.0.1',)

if USE_DJANGO_EVOLUTION:
    INSTALLED_APPS += ('django_evolution',)

if USE_DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',) 
    INSTALLED_APPS += ('debug_toolbar',)
