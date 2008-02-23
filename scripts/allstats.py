#!/usr/bin/env python
""" This script dumps the entire Statistics table on 
    a HTML page. """

import sys
sys.path.append('../')
from database import *

print "Content-type: text/html; charset=UTF-8\n"

res = Statistics.select()
print "<table>"
for stat in list(res):
    print "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % \
           (stat.Module, stat.Type, stat.Domain, stat.Branch, stat.Language, stat.Translated, stat.Fuzzy, stat.Untranslated)
print "</table>"
