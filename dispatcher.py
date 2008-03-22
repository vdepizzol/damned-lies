#!/usr/bin/python

import os
import re
import traceback
import utils
import defaults
import l10n

_ = l10n.gettext

from Cheetah.Template import Template

class DamnedError(Exception):
    pass

class DamnedNotHandledError(Exception):
    def __str__(self):
        return "This request cannot be handled by DamnedRequest."

class DamnedUnsupportedTypeError(Exception):
    def __str__(self):
        return ("Unsupported return type requested "
                +"(only 'html' and 'xml' are accepted).")

class DamnedTemplate(Template):
    def __init__(self, *args, **kw):
        content = open(kw['file'], 'r').read().decode('utf-8')
        kw['source'] = content
        if not kw.has_key('filter'):
            kw['filter'] = l10n.MyFilter
        del kw['file']
        Template.__init__(self, *args, **kw)
        self._ = l10n.gettext
        self.ngettext = l10n.ngettext
        self.rtl = (defaults.language in defaults.rtl_languages)
        self.webroot = defaults.webroot

class DamnedRequest:
    def __init__(self, template=None, xmltemplate=None):
        l10n.set_language()
        self.templatefile = template
        self.xmlfile = xmltemplate
        self._variables = {}

    def __setattr__(self, key, value):
        if key in ['_variables', 'request', 'templatefile', 'xmlfile']:
            self.__dict__[key] = value
            return
        else:
            self._variables[key] = value

    def render_by_request(self):
        if self.request.endswith('.xml'):
            self.request = self.request[:-4]
            self.render('xml')
        else:
            try:
                self.render('html')
            except Exception, e:
                self.render_html_error(e)

    def render(self, type='html', parameter=None):
        if type=='xml':
            tmpl = DamnedTemplate(file=self.xmlfile)
            content_type = 'application/xml'
        elif type=='html':
            tmpl = DamnedTemplate(file=self.templatefile)
            content_type = 'text/html'
        else:
            raise DamnedUnsupportedTypeError

        for var in self._variables:
            tmpl.__dict__[var] = self._variables[var]

        print "Content-type: %s; charset=UTF-8\n" % (content_type)
        print unicode(tmpl).encode('utf-8')
        global utils
        if type == 'html':
            print utils.TemplateInspector(tmpl)
    
    def render_html_error(self, err):
        print "Content-type: text/html; charset=UTF-8\n"
        print "<html><head><title>Damned Lies error</title><link rel='stylesheet' href='%s/data/layout.css'/></head>\n" % defaults.webroot
        print "<body><div id='header'><h1>Damned Lies</h1><p>&nbsp;</p></div>"
        print "<div id='content'><p>Sorry, an error occurred while processing the Web page.</p>\n"
        print "<p>Error: %s</p>" % str(err)
        if defaults.DEBUG:
            print "<pre>%s</pre>" % traceback.format_exc()
        print "<p>Return to <a href='%s/'>Home page</a></p>" % defaults.webroot
        print "</div></body></html>"

class RequestMapper:
    def __init__(self, base='/'):
        if 'PATH_INFO' in os.environ:
            self.fullrequest = os.getenv("PATH_INFO")
        else:
            self.fullrequest = '/'
        if self.fullrequest.endswith('/') and self.fullrequest != '/':
            self.fullrequest = self.fullrequest[:-1]
        if self.fullrequest.startswith(base):
            self.fullrequest = self.fullrequest[len(base):]
        else:
            raise DamnedNotHandledError
        self.requests = []

    def addRequest(self, path, request):
        """Add a request handler for a set of locations.

        `path` represents a regular expression to match for every request.
        If it contains a parenthesised match, it is forwarded to DamnedRequest.
        `request` is a DamnedRequest used to process the entry when matched.
        """
        path_re = re.compile(path)
        self.requests.append( (path_re, request) )

    def handleAll(self):
        self.requests.reverse()
        for (path_re, request) in self.requests:
            path_match = path_re.match(self.fullrequest)
            if path_match:
                if len(path_match.groups()):
                    parameter = path_match.group(1)
                else:
                    parameter = ''
                request.request = parameter
                request.render_by_request()
                return

        # No match
        print ("Status: 404 Doesn't exist\nContent-type: text/html\n\n" +
               "<html><body><h1>Unknown page</h1></body></html>")

