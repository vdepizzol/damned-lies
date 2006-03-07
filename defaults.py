#!/usr/bin/env python

# When in STRINGFREEZE, set this to 1 to send notifications to gnome-i18n@gnome.org on any POT changes
STRINGFREEZE = 1
notifications_to = 'gnome-i18n@gnome.org'
notifications_to = 'danilo@avet.kvota.net'

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


# Directory to checkout source code and dump dead bodies to
scratchdir = u"/tmp/gnome-stats"

# Directory to hold resulting POT/PO files
potdir = u"/tmp/gnome-stats/POT/"


# Web root directory
webroot = '/~danilo/damned-lies'

database_connection = 'sqlite:' + scratchdir + '/database.db'

DEBUG = 0

fuzzy_matching = 0

WHEREAREWE = 'http://i18n-status.gnome.org/'
WHOAREWE = 'danilo@gnome.org'
