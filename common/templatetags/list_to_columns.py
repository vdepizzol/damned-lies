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

from django import template

register = template.Library()

class SplitListNode(template.Node):
    def __init__(self, list, cols, new_list):
        self.list = list
        self.cols = cols
        self.new_list = new_list

    def split_seq(self, list, cols=2):
        start = 0
        for i in xrange(cols):
            stop = start + len(list[i::cols])
            yield list[start:stop]
            start = stop

    def render(self, context):
        context[self.new_list] = self.split_seq(context[self.list], int(self.cols))
        return ''

def list_to_columns(parser, token):
    """Parse template tag: {% list_to_columns list as new_list 2 %}"""
    bits = token.contents.split()
    if len(bits) != 5:
        raise template.TemplateSyntaxError, "list_to_columns list as new_list 2"
    if bits[2] != 'as':
        raise template.TemplateSyntaxError, "second argument to the list_to_columns tag must be 'as'"
    return SplitListNode(bits[1], bits[4], bits[3])
list_to_columns = register.tag(list_to_columns)
