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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

def index(request):
    translator_credits = _("translator-credits")
    # FIXME Not sure the LANGUAGE_CODE test is useful
    if request.LANGUAGE_CODE == 'en' or translator_credits == "translator-credits":
        translator_credits = ''
    else:
        translator_credits = translator_credits.split('\n')

    context = {
        'pageSection': 'home',
        'translator_credits': translator_credits
    }
    return render_to_response('index.html', context, context_instance=RequestContext(request))
