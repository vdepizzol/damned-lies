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

import operator
from django.conf import settings
from django.utils.translation import ugettext as _, get_language
from languages.models import Language
try:
    import PyICU
    pyicu_present = True
except:
    pyicu_present = False

MIME_TYPES = {
    'json': 'application/json',
    'xml':  'text/xml'
}

def trans_sort_object_list(lst, tr_field):
    """Sort an object list with translated_name"""
    for l in lst:
        l.translated_name = _(getattr(l, tr_field))
    templist = [(obj_.translated_name.lower(), obj_) for obj_ in lst]
    if pyicu_present:
        collator = PyICU.Collator.createInstance(PyICU.Locale(str(get_language())))
        templist.sort(key=operator.itemgetter(0), cmp=collator.compare)
    else:
        templist.sort()
    return [obj_ for (key1, obj_) in templist]

def merge_sorted_by_field(object_list1, object_list2, field):
    """
    Each call returns the next item, sorted by field in ascending order or in
    descending order if the field name begins by a minus sign.

    >>> from datetime import datetime
    >>> import itertools
    >>> class Foo(object):
    ...     def __init__(self, num):
    ...         self.num = num
    ...     def __repr__(self):
    ...         return str(self.num)
    ...
    >>> l1 = (Foo(1), Foo(8), Foo(5))
    >>> l2 = (Foo(1), Foo(2), Foo(4), Foo(4), Foo(6))
    >>> merge_sorted_by_field(l1, l2, 'num')
    [1, 1, 2, 4, 4, 5, 6, 8]
    >>> merge_sorted_by_field(l1, l2, 'num')[:3]
    [1, 1, 2]
    >>> l1 = (Foo(3), Foo(9), Foo(5))
    >>> l2 = (Foo(6), Foo(4), Foo(4), Foo(2), Foo(1))
    >>> [el.num for el in merge_sorted_by_field(l1, l2, '-num')]
    [9, 6, 5, 4, 4, 3, 2, 1]
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

def imerge_sorted_by_field(object_list1, object_list2, field):
    """
    Each call returns the next item, sorted by field in ascending order or in
    descending order if the field name begins by a minus sign.

    This function is faster (only one comparison by iteration) and uses less
    memory than merge_sorted_by_field (iterator) but the lists of objects must
    be already sorted in the same order as field.

    >>> from datetime import datetime
    >>> import itertools
    >>> class Foo(object):
    ...     def __init__(self, num):
    ...         self.num = num
    ...     def __repr__(self):
    ...         return str(self.num)
    ...
    >>> l1 = (Foo(1), Foo(3), Foo(5))
    >>> l2 = (Foo(1), Foo(2), Foo(4), Foo(6), Foo(8))
    >>> [el.num for el in imerge_sorted_by_field(l1, l2, 'num')]
    [1, 1, 2, 3, 4, 5, 6, 8]
    >>> [el.num for el in itertools.islice(imerge_sorted_by_field(l1, l2, 'num'), 3)]
    [1, 1, 2]
    >>> l1 = []
    >>> [el.num for el in imerge_sorted_by_field(l1, l2, 'num')]
    [1, 2, 4, 6, 8]
    >>> l1 = (Foo(5), Foo(4), Foo(1))
    >>> l2 = (Foo(6), Foo(4), Foo(4), Foo(2), Foo(1))
    >>> [el.num for el in imerge_sorted_by_field(l1, l2, '-num')]
    [6, 5, 4, 4, 4, 2, 1, 1]
    """
    import operator

    if field is not None and field[0] == '-':
        # Reverse the sort order
        field = field[1:]
        op = operator.gt
    else:
        op = operator.lt

    iter1, iter2 = iter(object_list1), iter(object_list2)

    # Too many try/except couples to my taste but I don't know how to filter the
    # StopIteration to find the source.

    try:
        el1 = iter1.next()
    except StopIteration:
        # Finish the other list
        while True:
            el2 = iter2.next()
            yield el2

    try:
        el2 = iter2.next()
    except StopIteration:
        # Finish the other list
        while True:
            # el1 is already fetched
            yield el1
            el1 = iter1.next()

    while True:
        if op(getattr(el1, field), getattr(el2, field)):
            yield el1
            try:
                el1 = iter1.next()
            except StopIteration:
                # Finish the other list
                while True:
                    yield el2
                    el2 = iter2.next()
        else:
            yield el2
            try:
                el2 = iter2.next()
            except StopIteration:
                # Finish the other list
                while True:
                    yield el1
                    el1 = iter1.next()

def is_site_admin(user):
    return user.is_superuser or settings.ADMIN_GROUP in [g.name for g in user.groups.all()]

def get_user_locale(request):
    curlang = Language.get_language_from_ianacode(request.LANGUAGE_CODE)
    if curlang and curlang.locale == 'en':
        curlang = None
    return curlang

if __name__ == "__main__":
    import doctest
    doctest.testmod()
