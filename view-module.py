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

import database
import modules

import os, sys

import cgi
import cgitb; cgitb.enable()
from Cheetah.Template import Template

print "Content-type: text/html; charset=UTF-8\n"

print os.getenv("HTTP_PATH_INFO")

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
