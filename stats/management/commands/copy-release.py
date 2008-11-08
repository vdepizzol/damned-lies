# -*- coding: utf-8 -*-
#
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

from django.core.management.base import BaseCommand, CommandError
from stats.models import Release, Category, Module

class Command(BaseCommand):
    help = "Copy an existing release and use trunk branches"
    args = "RELEASE_TO_COPY, NEW_RELEASE"
    
    output_transaction = False

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("Usage: copy-release RELEASE_TO_COPY NEW_RELEASE")

        try:
            rel_to_copy = Release.objects.get(name=args[0])
        except:
            raise CommandError("No release named '%s'" % args[0])
        
        new_rel = Release(name=args[1], description=args[1], stringfrozen=False, status=rel_to_copy.status)
        new_rel.save()
        
        for cat in rel_to_copy.category_set.all():
            if not cat.branch.is_head():
                mod = Module.objects.get(pk=cat.branch.module.id)
                branch = mod.get_head_branch()
            else:
                branch = cat.branch
            new_rel.category_set.add(Category(release=new_rel, branch=branch, category=cat.category))
        
        print "New release '%s' created" % args[1]

