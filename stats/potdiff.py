#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2007 Danilo Segan <danilo@gnome.org>.
#
# This file is part of Damned Lies.
#
# Damned Lies is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Damned Lies is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Damned Lies; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Output differences between two POT files

USE_DIFFLIB = 0

def diff(pota, potb, only_additions = 0):
    """Returns a list of differing lines between two files."""
    f1 = open(pota, "r")
    data1 = f1.read()
    res1 = _parse_contents(data1)
    res1.sort()

    f2 = open(potb, "r")
    data2 = f2.read()
    res2 = _parse_contents(data2)
    res2.sort()

    if not USE_DIFFLIB:
        # since we are working with sorted data, we can speed up the process by doing compares ourselves
        # instead of using difflib stuff
        i, j = 0, 0
        result = []
        while i < len(res1) and j < len(res2):
            if res1[i] == res2[j]:
                i+=1; j+=1
            elif res1[i] < res2[j]:
                if not only_additions:
                    result.append("- " + res1[i])
                i+=1
            elif res1[i] > res2[j]:
                result.append("+ " + res2[j])
                j+=1
        #print "\n".join(result)
        return result
    else:
        import difflib
        d = difflib.Differ()
        result = list(d.compare(res1, res2))

        onlydiffs = []
        for line in result:
            if line[0]!=" ":
                onlydiffs.append(line)
                #print line
        return onlydiffs


def _parse_contents(contents):
    """Parse PO file data, returning a list of msgid's.

    It also supports msgctxt (GNU gettext 0.15) and plural forms,
    the returning format of each entry is:

         [msgctxt::]msgid[/msgid_plural]"""

    if len(contents) and contents[-1] != "\n": contents += "\n"

    # state machine for parsing PO files
    msgid = ""; msgstr = ""; msgctxt = ""; comment = ""; plural = ""; 
    in_msgid = in_msgstr = in_msgctxt = in_msgid_plural = in_plural = 0

    result = []
    enc = "UTF-8"

    lines = contents.split("\n")
    lines.append("\n")
    for line in lines:
        line = line.strip()

        if line == "":
            if in_msgstr and msgid != "":
                onemsg = ""
                
                if msgctxt: onemsg += ('"' + msgctxt + '"::')
                onemsg += ('"' + msgid + '"')
                if plural: onemsg += ('/"' + plural + '"')

                result.append(onemsg)

            elif in_msgstr and msgid == "":
                # Ignore PO header
                pass

            msgid = ""; msgstr = ""; msgctxt = ""
            in_msgid = 0; in_msgstr = 0; in_msgctxt = 0
            flags = []; sources = []; othercomments = {}
            plural = ""; plurals = []; in_msgid_plural = 0; in_plural = 0

        elif line[0] == "\"" and line[-1] == "\"":
            if in_msgid:
                if in_msgid_plural:
                    plural += line[1:-1]
                else:
                    msgid += line[1:-1]
            elif in_msgctxt:
                msgctxt += line[1:-1]
            elif in_msgstr:
                pass
            else:
                raise Exception()

        elif line[0] == "#":
            # Ignore any comments, flags, etc.
            continue

        elif line[:12] == "msgid_plural" and in_msgid:
            in_msgid_plural = 1
            plural = line[13:].strip()[1:-1]
        elif line[:5] == "msgid" and not in_msgid:
            in_msgctxt = 0
            in_msgid = 1
            msgid = line[6:].strip()[1:-1]
        elif line[:7] == "msgctxt" and not in_msgid:
            in_msgctxt = 1
            msgctxt = line[8:].strip()[1:-1]
        elif line[:7] == "msgstr[" and in_msgid_plural:
            in_msgstr = 1
            in_msgid = 0
            in_msgctxt = 0
        elif line[:6] == "msgstr" and in_msgid:
            in_msgstr = 1
            in_msgid = 0
            in_msgctxt = 0
        else:
            pass
    return result

if __name__ == "__main__":
    import sys
    print "\n".join(diff(sys.argv[1], sys.argv[2]))
    
