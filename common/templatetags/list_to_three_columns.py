# -*- coding: utf-8 -*-
#
# Based on http://www.djangosnippets.org/snippets/889/
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>
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

"""Splits query results list into multiple sublists for template display.
   The order is column 1, then 3 and 2 to respect the CSS order."""
from django import template

register = template.Library()

class SplitListNode(template.Node):
    def __init__(self, list, new_list):
        self.list = list
        self.new_list = new_list

    def split_seq(self, list):
        # Simpler as a loop (KISS)
        len_col1 = len(list[0::3])
        len_col2 = len(list[1::3])
        len_col3 = len(list[2::3])
        # Column 1
        yield list[0:len_col1]
        # Column 3
        yield list[len_col1+len_col2:len_col1+len_col2+len_col3]
        # Column 2
        yield list[len_col1:len_col1+len_col2]

    def render(self, context):
        context[self.new_list] = self.split_seq(context[self.list])
        return ''

def list_to_three_columns(parser, token):
    """Parse template tag: {% list_to_three_columns list as columns %}"""
    bits = token.contents.split()
    if bits[2] != 'as':
        raise TemplateSyntaxError, "second argument to the list_to_three_columns tag must be 'as'"
    return SplitListNode(bits[1], bits[3])
list_to_three_columns = register.tag(list_to_three_columns)
