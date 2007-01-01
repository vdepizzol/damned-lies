#!/usr/bin/env python
"""Migrate old translation-status.xml into new damned-lies
gnome-modules.xml.in and releases.xml.in.

Merges if they already exist (so as not to overwrite any
manually-input data)."""

import libxml2
import sys

def readXmlFile(filename):
    expand_all_entities = 1
    ctxt = libxml2.createFileParserCtxt(filename)
    ctxt.lineNumbers(1)
    if expand_all_entities:
        ctxt.replaceEntities(1)
    ctxt.parseDocument()
    doc = ctxt.doc()
    if doc.name != filename:
        print >> sys.stderr, "Error: I tried to open '%s' but got '%s' -- how did that happen?" % (filename, doc.name)
        return None
    return doc

def mapOldId(old = None):
    mapping = {
        'gnome-2.12' : 'gnome-2-12',
        'gnome-2.14' : 'gnome-2-14',
        'gnome-2.16' : 'gnome-2-16',
        'gnome-2.18' : 'gnome-2-18',
        'developer-libs' : 'platform',
        'desktop' : 'desktop',
        'admin' : 'admin',
        'office' : 'gnome-office',
        'extras' : 'gnome-extras'
        }
    if not old:
        return mapping
    else:
        if mapping.has_key(old):
            return mapping[old]
        else:
            return old

def findElementById(node, id):
    pass

def findElementByTag(node, tag, id=None):
    child = node.children
    while child:
        if child.name == tag:
            if not id or (id and child.hasProp('id') and child.prop('id') == id):
                return child
        child = child.next
    return None

def getOldReleases(doc):
    releases = {}
    modules = {}
    
    root = doc.getRootElement()
    node = root.children
    while node:
        if node.name == 'release':
            if node.hasProp('name') and node.prop('name') != 'HEAD':
                relid = mapOldId(node.prop('name'))
                if not releases.has_key(relid):
                    releases[relid] = { 'id': relid, 'description' : '', 'modules' : {}, 'categories': {} }

                child = node.children
                while child:
                    if child.name == 'group':
                        catid = mapOldId(child.prop('name'))
                        desc = findElementByTag(child, 'description')
                        if desc: catdesc = desc.content
                        else: catdesc = ''
                        releases[relid]['categories'][catid] = {
                            'id' : catid,
                            'description' : catdesc,
                            'modules' : {}
                            }
                    child = child.next
            elif node.hasProp('name') and node.prop('name') == 'HEAD':
                child = node.children
                while child:
                    if child.name == 'group':
                        catid = mapOldId(child.prop('name'))
                        desc = findElementByTag(child, 'description')
                        if desc: catdesc = desc.content
                        else: catdesc = ''
                        if not releases.has_key(catid):
                            releases[catid] = {
                                'id' : catid,
                                'description' : catdesc,
                                'modules' : {},
                                'categories' : {},
                                }
                    child = child.next
            else:
                print >>sys.stderr, "Warning: there is a <release> without the name attribute on line %d." % (node.lineNo())
        elif node.name=='module':
            modid = mapOldId(node.prop('name'))
            child = node.children
            while child:
                if child.name != 'version':
                    child = child.next
                    continue

                relid = mapOldId(child.prop('release'))
                if relid == 'HEAD':
                    relid = mapOldId(findElementByTag(child, 'component').prop('group'))
                    catid = None
                else:
                    catid = mapOldId(findElementByTag(child, 'component').prop('group'))

                try:
                    branch = findElementByTag(findElementByTag(child, 'component'), 'branch').prop('name')
                except:
                    print >>sys.stderr, "Warning: no branch found for module %s." % modid
                    branch = 'HEAD'

                if modules.has_key(modid):
                    mymod = modules[modid]
                    if not mymod['branch'].has_key(branch):
                        mymod['branch'][branch] = { 'domain' : {} }
                else:
                    mymod = { 'id' : modid,
                              'branch' : { branch : { 'domain' : {} } } }
                    modules[modid] = mymod

                module = { 'id' : modid,
                           'branch' : branch,
                           'domain' : {},
                           'document' : {} }

                component = child.children
                while component:
                    if component.name == 'component':
                        potbase = component.prop('name')
                        domid = findElementByTag(component, 'podir').prop('dir')
                        if findElementByTag(component, 'branch').prop('name') != branch:
                            print >>sys.stderr, "Warning: branch name mismatch for %s/%s/%s." % (modid, relid, potbase)
                        module['domain'][domid] = potbase
                        mymod['branch'][branch]['domain'][domid] = potbase
                    component = component.next
                if catid:
                    releases[relid]['categories'][catid]['modules'][modid] = module
                else:
                    releases[relid]['modules'][modid] = module
                
                
                child = child.next
        node = node.next

    releases['allmodules'] = modules
    return releases

def addModulesToNode(node, modules):
    for modid in modules.keys():
        module = modules[modid]
        modnode = findElementByTag(node, 'module', modid)
        if not modnode:
            modnode = libxml2.newNode('module')
            modnode.newProp('id', modid)
            node.addChild(modnode)

        if module['branch'] != 'HEAD':
            if modnode.hasProp('branch'):
                modnode.setProp('branch', module['branch'])
            else:
                modnode.newProp('branch', module['branch'])
        else:
            if modnode.hasProp('branch'):
                modnode.setProp('branch', None)
                
            
        
        

def updateNewReleases(doc, oldrels):
    root = doc.getRootElement()
    for relid in oldrels.keys():
        rel = findElementByTag(root, 'release', relid)
        if not rel:
            rel = libxml2.newNode('release')
            root.addChild(rel)
            rel.newProp('id', relid)

        oldrel = oldrels[relid]
        if oldrel.has_key('description') and oldrel['description']:
            desc = findElementByTag(rel, '_description')
            if not desc:
                rel.newChild(None, '_description', oldrel['description'])

        for catid in oldrel['categories'].keys():
            cat = oldrel['categories'][catid]
            catnode = findElementByTag(rel, 'category', catid)
            if not catnode:
                catnode = libxml2.newNode('category')
                catnode.newProp('id', catid)
                rel.addChild(catnode)
            if cat.has_key('description') and cat['description']:
                desc = findElementByTag(catnode, '_description')
                if not desc:
                    rel.newChild(None, '_description', cat['description'])

            #from pprint import pprint
            #pprint(oldrel['modules'])
            addModulesToNode(catnode, cat['modules'])

        addModulesToNode(rel, oldrel['modules'])
                
def updateModules(doc, oldmods):
    root = doc.getRootElement()
    for modid in oldmods.keys():
        modnode = findElementByTag(root, 'module', modid)
        if not modnode:
            modnode = libxml2.newNode('module')
            root.addChild(modnode)
            modnode.newProp('id', modid)

        module = oldmods[modid]
        if module.has_key('description') and oldrel['description']:
            desc = findElementByTag(rel, '_description')
            if not desc:
                rel.newChild(None, '_description', oldrel['description'])

        for branch in module['branch']:
            brnode = findElementByTag(modnode, 'branch', branch)
            if not brnode:
                brnode = libxml2.newNode('branch')
                brnode.newProp('id', branch)
                modnode.addChild(brnode)
                
            if len(module['branch'][branch]['domain']) != 1 or not module['branch'][branch]['domain'].has_key('po'):
                for domain in module['branch'][branch]['domain']:
                    dnode = findElementByTag(brnode, 'domain', domain)
                    if not dnode:
                        dnode = libxml2.newNode('domain')
                        dnode.newProp('id', domain)
                        brnode.addChild(dnode)
                    if dnode.hasProp('potbase'):
                        if module['branch'][branch]['domain'][domain] == modid:
                            dnode.setProp('potbase', None)
                        else:
                            dnode.setProp('potbase', module['branch'][branch]['domain'][domain])
                    else:
                        if module['branch'][branch]['domain'][domain] != modid:
                            dnode.newProp('potbase', module['branch'][branch]['domain'][domain])
    

if __name__ == '__main__':
    from pprint import pprint
    if len(sys.argv)!=4:
        print >> sys.stderr, "Invalid syntax: use\n\t%s <OLD-STATUS-FILE> <NEW-RELEASES-FILE> <NEW-MODULES-FILE>\n" % sys.argv[0]
        sys.exit(1)

    libxml2.keepBlanksDefault(0)
    
    oldf = readXmlFile(sys.argv[1])
    olddata = getOldReleases(oldf)
    allmods = olddata['allmodules']
    #pprint(olddata)
    del olddata['allmodules']

    newr = readXmlFile(sys.argv[2])
    updateNewReleases(newr, olddata)
    newr.saveFormatFileEnc(sys.argv[2], 'utf-8', True)
    #print newr.serialize('utf-8')

    newm = readXmlFile(sys.argv[3])
    updateModules(newm, allmods)
    newm.saveFormatFileEnc(sys.argv[3], 'utf-8', True)
    #print newm.serialize('utf-8')
