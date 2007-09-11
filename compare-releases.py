#!/usr/bin/env python

import defaults

from releases import Releases, get_aggregate_stats

# Percentage which qualifies a language to be considered 'supported'
supported_limit = 80

if __name__ == "__main__":
    import sys, os
    if len(sys.argv)>=2:
        if os.access(defaults.modules_xml, os.R_OK):
            defaults.DEBUG = 0
            releases = sys.argv[1:]
            for release in releases:
                status = get_aggregate_stats(release)

                languages = 0
                total = 0

                for stats in status:
                    mytotal = (stats['ui_translated'] + stats['ui_fuzzy'] +
                               stats['ui_untranslated'])
                    if (100*stats['ui_translated']/mytotal >= supported_limit):
                        languages += 1
                    if mytotal > total:
                        total = mytotal
                print "%s: %d langs, %d msgs" % (release, languages, total)
        else:
            print "Usage:\n\t%s RELEASE1 [RELEASE2]...\n" % (sys.argv[0])
    else:
        print "Usage:\n\t%s RELEASE1 [RELEASE2]...\n" % (sys.argv[0])

