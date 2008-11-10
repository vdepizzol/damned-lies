from django.conf import settings
import os

DATABASE_ENGINE = getattr(settings, "DATABASE_ENGINE")
DEBUG = getattr(settings, "DEBUG", True)
WHEREAREWE = 'http://l10n.gnome.org/'
WHOAREWE = 'danilo@gnome.org'

# When in STRINGFREEZE, where to send notifications (gnome-i18n@gnome.org) on any POT changes
NOTIFICATIONS_TO = 'gnome-i18n@gnome.org'

# Local directories
SCRATCHDIR = ""
POTDIR = os.path.join(SCRATCHDIR, "POT")

