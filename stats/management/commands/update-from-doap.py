import sys
from django.core.management.base import BaseCommand

from stats.models import Module
from stats.doap import update_doap_infos

class Command(BaseCommand):
    help = "Update module information from doap file"
    args = "MODULE"

    def handle(self, *args, **options):
        if len(args) == 0:
            sys.stderr.write("You must provide at least one module name for this command.\n")
            sys.exit(1)

        for mod_name in args:
            try:
                mod = Module.objects.get(name=mod_name)
            except Module.DoesNotExist:
                sys.stderr.write("No module named '%s'. Ignoring.\n" % mod_name)
                continue
            update_doap_infos(mod)
            sys.stdout.write("Module '%s' updated from its doap file.\n" % mod_name)
