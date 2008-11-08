# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2007 Danilo Segan <danilo@gnome.org>.
# Copyright (c) 2008 Claude Paroz <claude@2xlibre.net>.
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

from django.utils.translation import ugettext as _

def trans_sort_object_list(lst, tr_field):
    """ Sort an object list with translated_name """
    for l in lst:
        l.translated_name = _(getattr(l, tr_field))
    templist = [(obj_.translated_name.lower(), obj_) for obj_ in lst]
    templist.sort()
    return [obj_ for (key1, obj_) in templist]
