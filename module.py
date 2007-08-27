#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2005 Danilo Šegan <danilo@gnome.org>.
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
#

# CGI script to display a single module and it's info

import defaults

from database import *
import modules
import teams
import utils
import l10n
import os, sys

from dispatcher import DamnedRequest


from time import tzname
from utils import compare_by_fields

def compare_stats(a, b):
    return compare_by_fields(a, b, ['translated', 'language_name'])

def compare_module_names(a, b):
    global allmodules
    return -utils.compare_by_fields(a, b, ['description', 'id'], allmodules.modules)

def compare_branches(a, b):
    if a=="HEAD":
        return -1
    elif b=="HEAD":
        return 1
    else:
        return cmp(a, b)*-1

class ListModulesRequest(DamnedRequest):
    def __init__(self, template=None, xmltemplate=None):
        global allmodules
        DamnedRequest.__init__(self, template, xmltemplate)
        allmodules = modules.XmlModules()
        moduleids = allmodules.keys()
        moduleids.sort(compare_module_names)
        self.modids = moduleids
        self.modules = allmodules

class ModulePageRequest(DamnedRequest):
    def render(self, type='html'):
        allmodules = modules.XmlModules()
        moduleids = allmodules.keys()
        moduleid = self.request
        if moduleid not in moduleids:
            raise Exception, "Module not found"

        module = allmodules[moduleid]

        for branch in module["branch"]:
            trdomains = module["branch"][branch]['domain'].keys()
            documents = module["branch"][branch]['document'].keys()
            for trdomain in trdomains:
                here = module["branch"][branch]['domain'][trdomain]
                here['statistics'] = []
                self.get_stats_for(here, module, trdomain, branch, 'ui')
                here['statistics'].sort(compare_stats) # FIXME: Allow different sorting criteria

                if len(here["statistics"])==0 and (not here.has_key('pot_size') or here['pot_size']==0):
                    del module["branch"][branch]["domain"][trdomain]

            for document in documents:
                here = module["branch"][branch]['document'][document]
                here['statistics'] = []
                if defaults.DEBUG: print >>sys.stderr, 'get_stats_for(', module["id"], ',', document, ',', branch, ',', 'doc)'
                self.get_stats_for(here, module, document, branch, 'doc')
                here['statistics'].sort(compare_stats) # FIXME: Allow different sorting criteria

                if (len(here["statistics"])==0 and
                    (not here.has_key('pot_size') or (here.has_key('pot_size') and here['pot_size']==0))):
                    #import pprint
                    #print >>sys.stderr, pprint.pformat(here)
                    del module["branch"][branch]["document"][document]
        self.module = module
        branches = module["branch"].keys()
        branches.sort(compare_branches)
        self.branches = branches

        DamnedRequest.render(self, type)



    def get_stats_for(self, here, module, trdomain, branch, type,
                      sortorder='name'):
        if type == 'doc':
            trdomain = here['potbase']
        res = Statistics.select(AND(Statistics.q.Module == module["id"],
                                    Statistics.q.Domain == trdomain,
                                    Statistics.q.Branch == branch,
                                    Statistics.q.Language == None,
                                    Statistics.q.Type == type),
                                orderBy="-date")
        if res and res.count()>0:
            pot = res[0]
            here['pot_size'] = pot.Untranslated
            here['updated'] = pot.Date.strftime("%Y-%m-%d %H:%M:%S ")+tzname[0]

            here['pot_messages'] = []
            for msg in pot.Messages:
                here['pot_messages'].append({'type' : msg.Type, 'content' : l10n.gettext(msg.Description)})

            here['statistics'] = []
            langres = teams.TranslationLanguages(show_hidden=1)
            #langres = {}

            allstats = Statistics.select(AND(Statistics.q.Module == module["id"],
                                             Statistics.q.Domain == trdomain,
                                             Statistics.q.Branch == branch,
                                             Statistics.q.Type == type),
                                         orderBy="-translated")
            for po in allstats:
                mylang = po.Language
                if not mylang: continue
                if mylang and langres.has_key(mylang):
                    langname = langres[mylang]
                    if not langname: continue
                else:
                    langname = ""

                new = {
                    'code' : mylang,
                    'translated' : po.Translated,
                    'fuzzy' : po.Fuzzy,
                    'untranslated' : po.Untranslated,
                    'language_name' : langname,
                    'updated' : po.Date.strftime("%Y-%m-%d %H:%M:%S ")+tzname[0],
                    }
                if here['pot_size']:
                    new['percentages'] = { 'translated' : 100*po.Translated/here['pot_size'],
                                           'untranslated' : 100*po.Untranslated/here['pot_size'], }
                    new['percentages']['fuzzy'] = 100 - new['percentages']['translated'] - new['percentages']['untranslated']
                    new['supportedness'] = 100*po.Translated/here['pot_size'];

                new['po_error'] = ''
                new['po_messages'] = []
                for msg in po.Messages:
                    new['po_messages'].append({'type': msg.Type, 'content': msg.Description})
                    if msg.Type=='error':
                        new['po_error'] = 'error'
                        new['po_error_message'] = l10n.gettext(msg.Description)
                    elif msg.Type=='warn' and new['po_error'] != 'error':
                        new['po_error'] = 'warn'
                        new['po_error_message'] = l10n.gettext(msg.Description)
                    elif msg.Type=='info' and not new['po_error']:
                        new['po_error'] = 'info'
                        new['po_error_message'] = l10n.gettext(msg.Description)


                here['statistics'].append(new)

        else:
            # Can't find database entries for this branch, unset it
            del here
