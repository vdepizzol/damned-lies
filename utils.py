#!/usr/bin/env python

def js_escape(string):
    return string.replace('"', '\\"')


# CheetahTemplate power stuff: similar to Smarty's debug console
def TemplateInspector(template):
    """Inspects all template variables and outputs them in a separate window using JavaScript."""
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
        _debug_console.document.write('<HTML><TITLE>Debug Console_'+self.name+'</TITLE><BODY bgcolor=#ffffff style="font-size:70%;"><PRE>');
"""

    import pprint
    for line in pprint.pformat(result).splitlines():
        output += '_debug_console.document.write("' + js_escape(line + '\\n') + '");' + "\n"

    output += """
	_debug_console.document.write("</BODY></HTML>");
	_debug_console.document.close();
</SCRIPT>"""

    return output
