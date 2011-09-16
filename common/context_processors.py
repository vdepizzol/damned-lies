# -*- coding: utf-8 -*-
from django.conf import settings

def utils(request):
    return {'bug_url': settings.ENTER_BUG_URL}
