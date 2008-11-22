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
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth import login, authenticate, logout
from django.conf import settings


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

def site_login(request):
    """ Site-specific login page. Not named 'login' to not confuse with auth.login """
    messages = []
    referer = None
    openid_path = ''
    if request.method == 'POST':
        if request.POST.has_key('logout') and request.POST['logout']:
            logout(request)
            messages.append(_("You have been logged out."))
        elif request.POST.has_key('username'):
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    message = _("You have been successfully logged in.")
                    user.message_set.create(message=message)
                    if request.POST['referer']:
                        return HttpResponseRedirect(request.POST['referer'])
                    else:
                        return HttpResponseRedirect(reverse("home"))
                else:
                    messages.append(_("We're sorry, but your account has been disabled."))
            else:
                messages.append(_("Login unsuccessful. Please verify your username and password."))
    else:
        referer = request.META.get('HTTP_REFERER', None)

    if 'django_openid' in settings.INSTALLED_APPS:
        openid_path = '/openid/'
    context = {
        'pageSection': 'home',
        'openid_path': openid_path,
        'messages': messages,
        'referer': referer,
    }
    return render_to_response('login.html', context, context_instance=RequestContext(request))
