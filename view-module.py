#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2005 Danilo Šegan <danilo@gnome.org>.
#
# This file is part of Gnome-Stats.
#
# Gnome-Stats is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Gnome-Stats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gnome-Stats; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# CGI script to display a single module and it's info

import defaults

from database import *
import modules
import teams
import utils

import os, sys

import cgi
import cgitb; cgitb.enable()
from Cheetah.Template import Template

print "Content-type: text/html; charset=UTF-8\n"



def get_stats_for(here, module, trdomain, branch, type, sortorder='name'):
    res = Statistics.select(AND(Statistics.q.Module == module["id"],
                                Statistics.q.Domain == trdomain,
                                Statistics.q.Branch == branch,
                                Statistics.q.Language == None,
                                Statistics.q.Type == type),
                            orderBy="-date")
    if res and res.count()>0:
        pot = res[0]
        here['pot_size'] = pot.Untranslated
        here['updated'] = pot.Date.strftime("%Y-%m-%d %H:%M:%S")

        here['pot_messages'] = []
        for msg in pot.Messages:
            here['pot_messages'].append({'type' : msg.Type, 'content' : msg.Description})

        here['statistics'] = []
        langres = teams.TranslationLanguages()
        #langres = {}

        allstats = Statistics.select(AND(Statistics.q.Module == module["id"],
                                         Statistics.q.Domain == trdomain,
                                         Statistics.q.Branch == branch,
                                         Statistics.q.Type == type),
                                     orderBy="-translated")
        for po in allstats:
            mylang = po.Language
            if not mylang: continue
            if langres.has_key(mylang):
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
                'updated' : po.Date.strftime("%Y-%m-%d %H:%M:%S"),
                }
            if here['pot_size']:
                new['percentages'] = { 'translated' : 100*po.Translated/here['pot_size'],
                                       'untranslated' : 100*po.Untranslated/here['pot_size'], }
                new['percentages']['fuzzy'] = 100 - new['percentages']['translated'] - new['percentages']['untranslated']
                new['supportedness'] = "%.0f" % (100.0*po.Translated/here['pot_size']);

            new['po_error'] = ''
            new['po_messages'] = []
            for msg in po.Messages:
                new['po_messages'].append({'type': msg.Type, 'content': msg.Description})
                if msg.Type=='error':
                    new['po_error'] = 'error'
                    new['po_error_message'] = msg.Description
                elif msg.Type=='warn' and new['po_error'] != 'error':
                    new['po_error'] = 'warn'
                    new['po_error_message'] = msg.Description
                elif msg.Type=='info' and not new['po_error']:
                    new['po_error'] = 'info'
                    new['po_error_message'] = msg.Description


            here['statistics'].append(new)

    else:
        # Can't find database entries for this branch, unset it
        del here


def compare_stats(a, b):
    res = cmp(float(b['supportedness']), float(a['supportedness']))
    if not res:
        return cmp(b['language_name'], a['language_name'])
    else:
        return res

def go_go():
    moduleid = os.getenv("PATH_INFO")[1:]
    allmodules = modules.XmlModules()
    if moduleid in allmodules:
        module = allmodules[moduleid]

        for branch in module["cvsbranches"]:
            trdomains = module["cvsbranches"][branch]['translation_domains'].keys()
            documents = module["cvsbranches"][branch]['documents'].keys()
            for trdomain in trdomains:
                here = module["cvsbranches"][branch]['translation_domains'][trdomain]
                here['statistics'] = []
                get_stats_for(here, module, trdomain, branch, 'ui')
                here['statistics'].sort(compare_stats) # FIXME: Allow different sorting criteria

                if len(here["statistics"])==0 and (not here.has_key('pot_size') or here['pot_size']==0):
                    del module["cvsbranches"][branch]["translation_domains"][trdomain]

            for document in documents:
                here = module["cvsbranches"][branch]['documents'][document]
                here['statistics'] = []
                get_stats_for(here, module, document, branch, 'doc')
                here['statistics'].sort(compare_stats) # FIXME: Allow different sorting criteria

                if len(here["statistics"])==0 and (not here.has_key('pot_size') or here['pot_size']==0):
                    del module["cvsbranches"][branch]["documents"][document]

        html = Template(file="templates/module.tmpl")
        html.webroot = defaults.webroot
        html.module = module
        print html
        print utils.TemplateInspector(html)
    else:
        # List all modules
        html = Template(file="templates/list-modules.tmpl")
        html.webroot = defaults.webroot
        html.modules = allmodules
        print html
        print utils.TemplateInspector(html)
        

import profile

go_go()
#profile.run('go_go()', 'profile2-data')

# form = cgi.FieldStorage()

# if form.getlist("document"):
#     docid = form.getlist("document")[0]
#     html = Template(file="templates/document.tmpl")
#     html.logged_in = login.IsLoggedIn()
#     doc = Document(id = docid)
#     if doc:
#         html.document = doc
#         print html
# elif form.getlist("unit"):
#     unitid = form.getlist("unit")[0]
#     html = Template(file="templates/show.tmpl")
#     html.logged_in = login.IsLoggedIn()
#     unit = EditingUnit(id = unitid)
#     if unit:
#         html.unit = unit
#         print html
