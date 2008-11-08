from django.core.management.base import NoArgsCommand
from django.core.management.commands import compilemessages
from optparse import make_option
import os
import shutil

class Command(NoArgsCommand):
    help = "Compile translations of djamnedlies"
    args = ""
    
    output_transaction = False

    def handle(self, **options):
        # Copy all po/ll.po files in locale/ll/LC_MESSAGES/django.po
        podir = os.path.abspath('po')
        for pofile in os.listdir(podir):
            if pofile[-3:] != ".po":
                continue
            lang_code = pofile[:-3]
            localedir = os.path.join(os.path.abspath('locale'), lang_code, 'LC_MESSAGES')
            if not os.path.isdir(localedir):
                os.makedirs(localedir)
            shutil.copy(os.path.join(podir, pofile), os.path.join(localedir, 'django.po'))
        
        # Run compilemessages -l ll
        compilemessages.compile_messages()

