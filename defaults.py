#!/usr/bin/env python

# Directory to checkout source code and dump dead bodies to
scratchdir = u"/home/danilo/cvs/gnom"

# Web root directory
webroot = '/~danilo/damned-lies'

# SQLObject database connection string
database_connection = 'sqlite:' + scratchdir + '/database.db'
database_connection = 'mysql://damned:lozinka@localhost/damned_lies'

# whether to generate translated XML documentation (might slow down the process significantly)
# they'll be put into os.path.join(scratchdir,"xml")
generate_docs = 0

WHEREAREWE = 'http://i18n-status.gnome.org/'
WHOAREWE = 'danilo@gnome.org'

# Configuration files
modules_xml = "po/gnome-modules.xml"
releases_xml = "po/releases.xml"
teams_xml = "po/translation-teams.xml"
people_xml = "po/people.xml"

# When in STRINGFREEZE, where to send notifications (gnome-i18n@gnome.org) on any POT changes
notifications_to = 'gnome-i18n@gnome.org'
notifications_to = 'danilo@smorisa.kvota.net'

# Whether to use fuzzy matching (much slower, but better for translators), use 0 only when testing!
fuzzy_matching = 0

# Set DEBUG to 1 to print (too) many messages on stderr about progress
DEBUG = 1

# Set to 1 to show all data passed to CheetahTemplates
WEBDEBUG = 1



# WARNING:
#   You usually don't want to set most of the things below,
#   unless you are using Damned Lies for something other than GNOME


# Directory to hold resulting POT/PO files
import os.path
potdir = os.path.join(scratchdir, "POT")

# default to Gnome Bugzilla, product same as module ID and component "general"
bugzilla = {
    "baseurl" : u"http://bugzilla.gnome.org/",
    "xmlrpc" : u"http://bugzilla-test.gnome.org/xmlrpc.cgi",
    "product" : u"",
    "component" : u"general",
    }

# default to a single "po" directory containing UI translations, and module ID for POT name
translation_domains = {
    u"po" : {"description" : u"UI translations", "potbase": ""} # description, base potname
    }

# default to a single "help" document containing User Guide
documents = {
    u"help" : {"description" : u"User Guide", "potbase" : "" }
    }

# default to anonyomus Gnome CVS
cvsroot = u":pserver:anonymous@anoncvs.gnome.org:/cvs/gnome"
cvsweb = u"http://cvs.gnome.org/viewcvs/%(module)s?only_with_tag=%(branch)s"
cvsbranch = {
    u"HEAD": { "translation_domains": translation_domains,
               "documents": documents,
               }
    }

# default to no maintainers for a module
maintainers = []

# Default language to fallback to
language = 'en'

# Right-to-left languages
rtl_languages = [ 'ar', 'fa', 'he', 'urd', 'yi']

# Dummy function for deferred translation (error messages)
# See http://docs.python.org/lib/node742.html
def N_(message): return message.replace("%s","###%s###")
