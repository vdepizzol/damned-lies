#!/usr/bin/env python

import defaults

from releases import Releases, get_aggregate_stats

supported_limit = 80

if __name__ == "__main__":
    import sys, os
    if len(sys.argv)>=2 and len(sys.argv)<=3:
        if os.access(defaults.modules_xml, os.R_OK):
            defaults.DEBUG = 0
            release_a = Releases(only_release=sys.argv[1])
            release_b = Releases(only_release=sys.argv[2])
            status_a = get_aggregate_stats(sys.argv[1]);
            status_b = get_aggregate_stats(sys.argv[2]);

            languages_a = languages_b = 0;
            total_a = total_b = 0;

            for stats in status_a:
                total = (stats['ui_translated'] + stats['ui_fuzzy'] +
                         stats['ui_untranslated'])
                if (100 * stats['ui_translated']/total >= supported_limit):
                    languages_a += 1
                if total > total_a:
                    total_a = total
            for stats in status_b:
                total = (stats['ui_translated'] + stats['ui_fuzzy'] +
                         stats['ui_untranslated'])
                if (100 * stats['ui_translated']/total >= supported_limit):
                    languages_b += 1
                if total > total_b:
                    total_b = total
            print "%s: %d langs, %d msgs" % (sys.argv[1], languages_a, total_a)
            print "%s: %d langs, %d msgs" % (sys.argv[2], languages_b, total_b)
        else:
            print "Usage:\n\t%s RELEASE1 RELEASE2\n" % (sys.argv[0])
    else:
        print "Usage:\n\t%s RELEASE1 RELEASE2\n" % (sys.argv[0])

