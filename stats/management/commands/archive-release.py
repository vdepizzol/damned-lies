import csv
import sys
import StringIO
from django.core.management.base import BaseCommand
from stats.models import Release, Statistics

class Command(BaseCommand):
    help = "Write statistics of a release in a CSV structure (stdout)"
    args = "RELEASE"

    def handle(self, *args, **options):
        if len(args) != 1:
            sys.stderr.write("You must provide one and only one release name as parameter of this command.\n")
            sys.exit(1)

        try:
            release = Release.objects.get(name=args[0])
        except Release.DoesNotExist:
            sys.stderr.write("The release name '%s' is not known.\n" % args[0])
            sys.exit(1)

        out = StringIO.StringIO()
        headers = ['Module', 'Branch', 'Domain', 'Language', 'Translated', 'Fuzzy', 'Untranslated']
        writer = csv.DictWriter(out, headers)
        header = dict(zip(headers, headers))
        writer.writerow(header)

        stats = Statistics.objects.filter(branch__category__release=release, language__isnull=False).select_related('branch__module', 'domain', 'language')
        for stat in stats:
            row = {
                'Module': stat.branch.module.name.encode('utf-8'),
                'Branch': stat.branch.name.encode('utf-8'),
                'Domain': stat.domain.name.encode('utf-8'),
                'Language': stat.language.locale,
                'Translated': stat.translated,
                'Fuzzy': stat.fuzzy,
                'Untranslated': stat.untranslated,
            }
            writer.writerow(row)
        return out.getvalue()
