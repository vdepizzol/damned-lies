import os
import re
from xml.etree.ElementTree import parse
from urllib import unquote

from people.models import Person

def parse_maintainers(doap_tree):
    maint_tags = doap_tree.getroot().findall("{http://usefulinc.com/ns/doap#}maintainer")
    pers_attrs = [
        "{http://xmlns.com/foaf/0.1/}name",
        "{http://xmlns.com/foaf/0.1/}mbox",
        "{http://api.gnome.org/doap-extensions#}userid"
    ]
    maintainers = []
    for maint in maint_tags:
        name, mbox, uid = [maint[0].find(attr) for attr in pers_attrs]
        maint = {'name': name.text, 'email': None, 'account': None}
        if mbox is not None:
            maint['email'] = unquote(mbox.items()[0][1].replace("mailto:", ""))
        if uid is not None:
            maint['account'] = uid.text
        maintainers.append(maint)
    return maintainers

def parse_homepage(doap_tree):
    homepage_tag = doap_tree.getroot().find("{http://usefulinc.com/ns/doap#}homepage")
    if homepage_tag is not None:
        return homepage_tag.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
    return None

def update_doap_infos(module):
    """ Should only be called inside an "update-stats" context of a master branch,
        so there is no need for any extra checkout/locking strategy """
    doap_path = os.path.join(module.get_head_branch().co_path(), "%s.doap" % module.name)
    if not os.access(doap_path, os.F_OK):
        return
    tree = parse(doap_path)

    # *********** Update maintainers
    def slugify(val):
        value = unicode(re.sub('[^\w\s-]', '', val).strip().lower())
        return re.sub('[-\s]+', '-', value)
    doap_maintainers = parse_maintainers(tree)
    current_maintainers = dict([(m.email or m.username, m) for m in module.maintainers.all()])

    # Using email or username as unique identifier
    for maint in doap_maintainers:
        maint_key = maint['email'] or maint['account'] or slugify(maint['name'])
        if maint_key in current_maintainers.keys():
            del current_maintainers[maint_key]
        else:
            # Add new maintainer
            query_param = {maint['email'] and 'email' or 'username': maint_key }
            try:
                pers = Person.objects.get(**query_param)
            except Person.DoesNotExist:
                pers = Person(username=maint['account'] or slugify(maint['name']), email=maint['email'] or '',
                              password='!', svn_account=maint['account'], last_name=maint['name'])
                pers.save()
            module.maintainers.add(pers)

    for key, maint in current_maintainers.items():
        # Drop maintainers not in doap file
        module.maintainers.remove(maint)

    # *********** Update homepage
    home = parse_homepage(tree)
    if home and home != module.homepage:
        module.homepage = home
        module.save()
