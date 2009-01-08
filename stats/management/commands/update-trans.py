import os
import shutil
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.commands import makemessages
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = "Update translations of djamnedlies ('en' is a special case, and generate damned-lies.pot)"
    args = "LANG_CODE"
    
    #option_list = BaseCommand.option_list + (
    #    make_option('--pot', action='store_true', dest='pot', default=False,
    #        help="create a pot file"),
    #)        

    output_transaction = False

    def handle(self, *args, **options):
        if len(args)!=1:
            return "You have to specify language code as first and only argument."
        lang_code = args[0]

        # Copy po/ll.po in locale/ll/LC_MESSAGES/django.po
        podir = os.path.abspath('po')
        localedir = os.path.join(os.path.abspath('locale'), lang_code, 'LC_MESSAGES')
        if lang_code != 'en':
            pofile = os.path.join(podir, '%s.po' % lang_code)
            if os.path.exists(pofile):
                if not os.path.isdir(localedir):
                    os.makedirs(localedir)
                shutil.copy(pofile, os.path.join(localedir, 'django.po'))
        else:
            pofile = os.path.join(podir, 'damned-lies.pot')
        
        # Extract DB translatable strings into database-content.py
        dbfile = os.path.join(os.path.abspath('.'), 'database-content.py')
        f=open(dbfile, 'w')
        query = """SELECT description FROM team UNION DISTINCT
                   SELECT name from language WHERE name <> locale UNION DISTINCT
                   SELECT description FROM domain UNION DISTINCT
                   SELECT description FROM module WHERE description <> name UNION DISTINCT
                   SELECT comment FROM module WHERE comment IS NOT NULL AND comment <> '' UNION DISTINCT
                   SELECT description FROM "release" """
        cursor = connection.cursor()
        if settings.DATABASE_ENGINE == 'mysql':
            cursor.execute("SET sql_mode='ANSI_QUOTES'")
        cursor.execute(query)
        for row in cursor.fetchall():
            if row[0] is not None and row[0] != '':
                f.write("_(u\"\"\"%s\"\"\")\n" % row[0].encode('utf-8'))
        f.close()

        # Run makemessages -l ll
        makemessages.make_messages(lang_code, verbosity=2, extensions=['.html'])
        
        # Delete database-content.py
        os.unlink(dbfile)
        
        # Copy locale/ll/LC_MESSAGES/django.po to po/ll.po
        shutil.copy(os.path.join(localedir, 'django.po'), pofile)
        
        return "po file for language '%s' updated." % lang_code


