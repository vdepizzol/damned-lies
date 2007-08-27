#!/usr/bin/env python

import defaults

def js_escape(string):
    return string.replace('"', '\\"')


# CheetahTemplate power stuff: similar to Smarty's debug console
def TemplateInspector(template):
    """Inspects all template variables and outputs them in a separate window using JavaScript."""
    if not defaults.WEBDEBUG:
        return ""
    
    from Cheetah.Template import Template
    blank = Template("")
    ignore = dir(blank)
    full = dir(template)
    result = {}
    for single in full:
        if single not in ignore and single[0]!='_':
            result[single] = template.__dict__[single]

    output = """<SCRIPT language=javascript>
	if( self.name == '' ) {
	   var title = 'Console';
	}
	else {
	   var title = 'Console_' + self.name;
	}
	_debug_console = window.open('',title.value,'width=680,height=600,resizable,scrollbars=yes');
        _debug_console.document.write('<HTML><TITLE>Debug Console'+self.name+'</TITLE><BODY bgcolor=#ffffff style="font-size:70%;"><PRE>');
"""

    import pprint
    for line in pprint.pformat(result).splitlines():
        output += '_debug_console.document.write("' + js_escape(line + '\\n') + '");' + "\n"

    output += """
	_debug_console.document.write("</BODY></HTML>");
	_debug_console.document.close();
</SCRIPT>"""

    return output


def not_found_404():
    import sys
    print "Content-Type: text/html"
    print "Status: 404 Not found\n"
    print "Can't tell what you want from me! :("
    sys.exit(1)

def getElementContents(node):
    nodelist = node.childNodes
    rc = ""
    for el in nodelist:
        if el.nodeType == el.TEXT_NODE:
            rc = rc + el.data
    return rc

def getElementText(node, element, default = 0):
    if not node.hasChildNodes():
        return default
    child = node.firstChild
    while child:
        if child.nodeType == child.ELEMENT_NODE and child.nodeName == element:
            return self.getElementContents(child)
        child = child.nextSibling
    return default


def getElementAttribute(node, attribute, default = 0):
    if not node.hasAttribute(attribute):
        ret = node.getAttribute(attribute)
        if ret:
            return ret
        else:
            return default
    else:
        return default

def compare_by_fields(a, b, fields, dict = None):
    af = bf = 0.0

    if dict:
        a = dict[a]
        b = dict[b]
    for field in fields:
        if a.has_key(field):
            try: # prefer numerical comparison
                af = float(a[field])
            except:
                af = a[field].lower()

        if b.has_key(field):
            try: # prefer numerical comparison
                bf = float(b[field])
            except:
                bf = b[field].lower()

        res = cmp(bf, af)
        if res:
            return res
    return res

