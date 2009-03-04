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
    """Sort an object list with translated_name"""
    for l in lst:
        l.translated_name = _(getattr(l, tr_field))
    templist = [(obj_.translated_name.lower(), obj_) for obj_ in lst]
    templist.sort()
    return [obj_ for (key1, obj_) in templist]

def merge_sorted_by_field(object_list1, object_list2, field):
    """
    Each call returns the next item, sorted by field in ascending order or in
    descending order if the field name begins by a minus sign.

    The lists of objects must be already sorted in the same order as field.

    >>> from datetime import datetime
    >>> import itertools
    >>> class Foo(object):
    ...     def __init__(self, num):
    ...         self.num = num
    ...     def __repr__(self):
    ...         return str(self.num)
    ...
    >>> l1 = (Foo(1), Foo(4), Foo(5))
    >>> l2 = (Foo(1), Foo(2), Foo(4), Foo(4), Foo(6))
    >>> merge_sorted_by_field(l1, l2, 'num')
    [1, 1, 2, 4, 4, 4, 5, 6]
    >>> merge_sorted_by_field(l1, l2, 'num')[:3]
    [1, 1, 2]
    >>> l1 = (Foo(5), Foo(4), Foo(1))
    >>> l2 = (Foo(6), Foo(4), Foo(4), Foo(2), Foo(1))
    >>> [el.num for el in merge_sorted_by_field(l1, l2, '-num')]
    [6, 5, 4, 4, 4, 2, 1, 1]
    """
    import itertools
    if field is not None and field[0] == '-':
        # Reverse the sort order
        field = field[1:]
        reverse = True
    else:
        reverse = False

    return sorted(itertools.chain(object_list1, object_list2),
                  key=lambda x: getattr(x, field),
                  reverse=reverse)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
