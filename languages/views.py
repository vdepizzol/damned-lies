# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Stéphane Raimbault <stephane.raimbault@gmail.com>
# Copyright (c) 2008-2011 Claude Paroz <claude@2xlibre.net>
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

from datetime import date, datetime
import os
import tarfile

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from common import utils
from languages.models import Language
from stats.models import Release, Statistics

def languages(request):
    languages = Language.objects.select_related("team").all()
    context = {
        'pageSection': "languages",
        'languages': utils.trans_sort_object_list(languages, 'name'),
    }
    return render(request, 'languages/language_list.html', context)

def language_all(request, locale, dtype):
    language = get_object_or_404(Language, locale=locale)
    stats = Statistics.get_lang_stats_by_type(language, dtype, release=None)
    context = {
        'pageSection': "languages",
        'language': language,
        'stats_title': {
            'ui':  _("UI Translations"),
            'ui-part': _("UI Translations (reduced)"),
            'doc': _("Documentation")}.get(dtype),
        'stats': stats,
        'scope': dtype.endswith('-part') and 'part' or 'full',
    }
    return render(request, 'languages/language_all_modules.html', context)

def release_archives(request, locale):
    """ This view is used to display archive release stats through Ajax call
        Only the HTML table is produced
    """
    language = get_object_or_404(Language, locale=locale)
    context = {
        'lang': language,
        'stats': language.get_release_stats(archives=True),
        'show_all_modules_line': False,
    }
    return render(request, 'languages/language_release_summary.html', context)

def language_release(request, locale, release_name, dtype):
    if locale == 'C':
        language = None
    else:
        language = get_object_or_404(Language, locale=locale)
    release = get_object_or_404(Release, name=release_name)
    stats = Statistics.get_lang_stats_by_type(language, dtype, release)
    context = {
        'pageSection': "languages",
        'language': language,
        'language_name': language and language.get_name() or _("Original strings"),
        'release': release,
        'stats_title': {
            'ui':  _("UI Translations"),
            'ui-part': _("UI Translations (reduced)"),
            'doc': _("Documentation")}.get(dtype),
        'stats': stats,
        'dtype': dtype,
        'scope': dtype.endswith('-part') and 'part' or 'full',
    }
    return render(request, 'languages/language_release.html', context)

def language_release_tar(request, locale, release_name, dtype):
    release = get_object_or_404(Release, name=release_name)
    language = get_object_or_404(Language, locale=locale)
    last_modif, file_list = release.get_lang_files(language, dtype)

    tar_filename = '%s.%s.%s.%s.tar.gz' % (release.name, dtype, language.locale, date.today())
    tar_directory = os.path.join(settings.POTDIR, 'tar')
    if not os.access(tar_directory, os.R_OK):
        os.mkdir(tar_directory)
    tar_path = os.path.join(tar_directory, tar_filename)
    if not os.access(tar_path, os.R_OK) or last_modif > datetime.fromtimestamp(os.path.getmtime(tar_path)):
        # Create a new tar file
        tar_file = tarfile.open(tar_path, 'w:gz')
        for f in file_list:
            tar_file.add(f, os.path.basename(f))
        tar_file.close()

    return HttpResponseRedirect("/POT/tar/%s" % tar_filename)

def language_release_xml(request, locale, release_name):
    """ This view create the same XML output than the previous Damned-Lies, so as
        apps which depend on it (like Vertimus) don't break.
        This view may be suppressed when Vertimus will be integrated in D-L. """
    language = get_object_or_404(Language, locale=locale)
    release = get_object_or_404(Release, name=release_name)
    stats = release.get_lang_stats(language)
    content = "<stats language=\"%s\" release=\"%s\">\n" % (locale, release_name)
    for catname, categ in stats['ui']['categs'].items():
        if catname != 'default':
            content += "<category id=\"%s\">" % catname
        # totals for category
        if catname in stats['doc']['categs']:
            content += "<doctranslated>%s</doctranslated>" % stats['doc']['categs'][catname]['cattrans']
            content += "<docfuzzy>%s</docfuzzy>" % stats['doc']['categs'][catname]['catfuzzy']
            content += "<docuntranslated>%s</docuntranslated>" % stats['doc']['categs'][catname]['catuntrans']
        content += "<translated>%s</translated>" % categ['cattrans']
        content += "<fuzzy>%s</fuzzy>" % categ['catfuzzy']
        content += "<untranslated>%s</untranslated>" % categ['catuntrans']
        # Modules
        for modname, mod in categ['modules']:
            branch_name, domains = mod.items()[0]
            content += "<module id=\"%s\" branch=\"%s\">" % (modname, branch_name)
            # DOC domains
            if catname in stats['doc']['categs'] and stats['doc']['categs'][catname]['modules']:
                for docmod in stats['doc']['categs'][catname]['modules']:
                    if docmod[0] == modname:
                        content += get_domain_stats(docmod[1].values()[0], "document")
            # UI stats
            content += get_domain_stats(domains, "domain")
            content += "</module>"
        # Add modules who have no ui counterparts
        if catname == 'dev-tools':
            try:
                mod = [m for m in stats['doc']['categs']['dev-tools']['modules'] if m[0] == 'gnome-devel-docs'][0][1]
                content += "<module id=\"gnome-devel-docs\" branch=\"%s\">" % mod.keys()[0]
                content += get_domain_stats(mod.values()[0], "document")
                content += "</module>"
            except:
                pass
        if catname == 'desktop':
            try:
                mod = [m for m in stats['doc']['categs']['desktop']['modules'] if m[0] == 'gnome-user-docs'][0][1]
                content += "<module id=\"gnome-user-docs\" branch=\"%s\">" % mod.keys()[0]
                content += get_domain_stats(mod.values()[0], "document")
                content += "</module>"
            except:
                pass

        if catname != 'default':
            content += "</category>"
    content += "</stats>"
    return HttpResponse(content, content_type='text/xml')

def get_domain_stats(mods, node_name):
    """ Iterate module domains to get stats """
    content = ""
    for dom_key, stat in mods:
        if dom_key == ' fake':
            continue
        content += "<%s id=\"%s\">" % (node_name, stat.domain.name)
        content += "<translated>%s</translated>" % stat.translated()
        content += "<fuzzy>%s</fuzzy>" % stat.fuzzy()
        content += "<untranslated>%s</untranslated>" % stat.untranslated()
        content += "<pofile>%s</pofile>" % stat.po_url()
        content += "<svnpath>%s</svnpath>" % stat.vcs_web_path()
        content += "</%s>" % node_name
    return content

# ********* Utility functions ******************
def clean_tar_files():
    """ Delete outdated tar.gz files generated by the language_release_tar view """
    tar_directory = os.path.join(settings.POTDIR, 'tar')
    if not os.path.exists(tar_directory):
        return
    for tarfile in os.listdir(tar_directory):
        if not tarfile.endswith("%s.tar.gz" % date.today()):
            os.remove(os.path.join(tar_directory, tarfile))
