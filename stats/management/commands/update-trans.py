import os
import re
import shutil
import itertools

from django.core.management.base import BaseCommand
from django.core.management.commands import makemessages
from django.db.models import F

from teams.models import Team
from languages.models import Language
from stats.models import Module, Domain, Release

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

        for value in itertools.chain(
            Team.objects.values_list('description', flat=True),
            Language.objects.exclude(name__exact=F('locale')).values_list('name', flat=True),
            Domain.objects.distinct().values_list('description', flat=True),
            Module.objects.exclude(name__exact=F('description')).values_list('description', flat=True),
            Module.objects.filter(comment__isnull=False).values_list('comment', flat=True),
            Release.objects.values_list('description', flat=True)):
            if value:
                value = re.sub(r'\r\n|\r|\n', '\n', value)
                f.write("_(u\"\"\"%s\"\"\")\n" % value.encode('utf-8'))
        f.close()

        # Run makemessages -l ll
        makemessages.make_messages(lang_code, verbosity=2, extensions=['.html'])

        # Delete database-content.py
        os.unlink(dbfile)

        # Copy locale/ll/LC_MESSAGES/django.po to po/ll.po
        shutil.copy(os.path.join(localedir, 'django.po'), pofile)

        return "po file for language '%s' updated." % lang_code
