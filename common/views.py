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
from django.contrib import messages
from django.conf import settings
from people.models import Person
from teams.models import Role
from people.forms import RegistrationForm
from languages.models import Language

def index(request):
    """ Homepage view """
    translator_credits = _("translator-credits")
    if translator_credits == "translator-credits":
        translator_credits = ''
    else:
        translator_credits = translator_credits.split('\n')

    curlang = Language.get_language_from_ianacode(request.LANGUAGE_CODE)
    if curlang.locale == 'en':
        curlang = None

    context = {
        'pageSection': 'home',
        'user_language': curlang,
        'translator_credits': translator_credits
    }
    return render_to_response('index.html', context, context_instance=RequestContext(request))

def site_login(request):
    """ Site-specific login page. Not named 'login' to not confuse with auth.login """
    referer = None
    openid_path = ''
    if request.method == 'POST':
        if 'logout' in request.POST and request.POST['logout']:
            logout(request)
            messages.success(request, _("You have been logged out."))
        elif 'username' in request.POST:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, _("You have been successfully logged in."))
                    if Role.objects.filter(person__username=user.username).count() < 1:
                        message = _("You have not joined any translation team yet. You can do it from <a href=\"%(url)s\">your profile</a>.") % {
                            'url': reverse('person_team_join'),
                        }
                        messages.info(request, message)
                    if 'referer' in request.POST:
                        return HttpResponseRedirect(request.POST['referer'])
                    else:
                        return HttpResponseRedirect(reverse("home"))
                else:
                    messages.error(request, _("We're sorry, but your account has been disabled."))
            else:
                messages.error(request, _("Login unsuccessful. Please verify your username and password."))
    else:
        referer = request.META.get('HTTP_REFERER', None)

    if 'django_openid' in settings.INSTALLED_APPS:
        openid_path = '/openid/'
    context = {
        'pageSection': 'home',
        'openid_path': openid_path,
        'referer': referer,
    }
    return render_to_response('login.html', context, context_instance=RequestContext(request))

def site_register(request):
    openid_path = ''
    if request.method == 'POST':
        form = RegistrationForm(data = request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect(reverse('register_success'))
    else:
        form = RegistrationForm()
    if 'django_openid' in settings.INSTALLED_APPS:
        openid_path = '/openid/'
    context = {
        'pageSection': 'home',
        'form': form,
        'openid_path': openid_path,
    }
    return render_to_response('registration/register.html', context, context_instance=RequestContext(request))

def activate_account(request, key):
    """ Activate an account through the link a requestor has received by email """
    try:
        person = Person.objects.get(activation_key=key)
    except Person.DoesNotExist:
        return render_to_response('error.html', {'error':"Sorry, the key you provided is not valid."})
    person.activate()
    messages.success(request, _("Your account has been activated."))
    return site_login(request)
