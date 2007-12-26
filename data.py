#!/usr/bin/env python

import copy
import re
import libxml2
import os
import defaults

def getModules(only = None):
    return readFromFile(defaults.modules_xml, only)

def getPeople(only = None): 
    return readFromFile(defaults.people_xml, only)

def getTeams(only = None, en = False): 
    return readFromFile(defaults.teams_xml, only, en)

def getReleases(only = None): 
    return readFromFile(defaults.releases_xml, only)

def readFromFile(filename, only_id = None, force_en = False):
    """Reads XML file or pickle-cached copy of it (while also keeping it up-to-date)."""
    import os

    if not force_en:
        myfilename = filename.replace('po/', 'po/'+defaults.language+'/')
        if os.access(myfilename, os.R_OK):
            filename = myfilename

    picklefile = filename + ".pickle"

    do_pickle = 0
    pickle_exists = 0
    try:
        pdate = os.stat(picklefile).st_mtime
        pickle_exists = 1
        fdate = os.stat(filename).st_mtime
        if pdate < fdate:
            do_pickle = 1
    except:
        # create a new pickle copy anyway
        do_pickle = 1

    import pickle
    if not do_pickle and pickle_exists:
        inp = open(picklefile, "rb")
        dict = pickle.load(inp)
        inp.close()
        return dict
    else:
        dom = libxml2.parseFile (filename)
        dict = _getContainerData (dom.getRootElement(), only_id)

        # we don't want a pickle file with a single entry
        if not only_id:
            try:
                out = open(picklefile, "wb")
                pickle.dump(dict, out)
                out.close()
            except:
                # ignore if we can't write out picklefile, it will only be slower
                import sys
                print >>sys.stderr, "Warning: can't write out pickle file '%s' for '%s'. Performance will suffer." % (picklefile, filename)

        return dict

    


def _getContainerData (node, only_id = None):
    data = {}
    defsDict = {}
    child = node.children
    while child:
        if child.type == 'element':
            if child.name == u'defaults':
                defsDict = _getDefaultsData (child)
            elif child.hasProp (u'id'):
                if only_id:
                    if child.prop(u'id') == only_id:
                        thingData = _getThingData (child, defsList=(defsDict,))
                        return { thingData[u'id'] : thingData }
                else:
                    thingData = _getThingData (child, defsList=(defsDict,))
                    data[thingData[u'id']] = thingData

            else:
                # FIXME: be more strict
                pass
        child = child.next
    return data

def _getDefaultsData (node, defsList=(), things={}):
    defsDict = {}
    thing = node.children
    while thing:
        if thing.type == 'element':
            defsDict[thing.name] = data = {}
            child = thing.children
            while child:
                if child.type == 'element':
                    key = child.name
                    if child.hasProp (u'id'):
                        if not data.has_key (key): data[key] = {}
                        newThing = _getThingData (child, defsList=defsList, things=things)
                        data[key][newThing[u'id']] = newThing
                    else:
                        if _node_is_text_only(child):
                            data[key] = _getString (child)
                        else:
                            data[key] = _getThingData (child)
                child = child.next
        thing = thing.next
    return defsDict

def _getThingData (node, defsList=(), things={}):
    data = {}
    defsDict = {}

    newDefsList = defsList

    newThings = copy.copy(things)
    newThings[node.name] = data

    if node.properties:
        for prop in node.properties:
            data[prop.name] = prop.content.decode('utf-8')

    if _node_is_text_only(node):
        data['content'] = node.content.decode('utf-8')
    else:
        child = node.children
        while child:
            if child.type == 'element':
                key = child.name
                if key == u'defaults':
                    defsDict = _getDefaultsData (child, defsList=defsList, things=things)
                    newDefsList = (defsDict,) + defsList
                elif child.hasProp (u'id'):
                    if not data.has_key (key): data[key] = {}
                    newThing = _getThingData (child, defsList=newDefsList, things=newThings)
                    data[key][newThing[u'id']] = newThing
                else:
                    if _node_is_text_only(child):
                        data[key] = _getString (child)
                    else:
                        data[key] = _getThingData (child)
            child = child.next

    _applyDefaultsList (data, node.name, newDefsList, things=newThings)

    return data

def _applyDefaultsList (data, dataType, defsList, things={}):
    for defs in defsList:
        if defs.has_key (dataType):
            _applyDefaultsData (data, dataType, defs[dataType],
                                defsList=defsList, things=things)

def _applyDefaultsData (data, dataType, defsDict, defsList=(), things={}):
    pat = re.compile('%\(([^)]*)\)')
    def subsFunc(match):
        str = match.group (1)
        this = things
        for k in str.split(u'/'):
            if this.has_key (k):
                this = this[k]
            else:
                return match.group (0)
        return this

    #print data
    #print "TYPE of defsDict: ", type(defsDict)

    if type(defsDict) == type(u''):
        val = defsDict
        if not data:
            data = pat.sub (subsFunc, val)
    else:
        for key in defsDict.keys():
            val = defsDict[key]
            if type(val) == type(u''):
                if not data.has_key (key):
                    data[key] = pat.sub (subsFunc, val)
            elif type(val) == type({}):
                if not data.has_key (key): data[key] = {}
                for i in defsDict[key].keys():
                    id = pat.sub (subsFunc, i)
                    if type(val[id]) == type(u''):
                        if not data[key].has_key (id):
                            data[key][id] = pat.sub (subsFunc, val[id])
                    else:
                        if not data[key].has_key (id): data[key][id] = {}
                        newThings = copy.copy(things)
                        newThings[key] = data[key][id]
                        _applyDefaultsData (data[key][id], key, defsDict[key][i],
                                        defsList=defsList, things=newThings)
                        _applyDefaultsList (data[key][id], key,
                                        defsList=defsList, things=newThings)
            else:
                #FIXME: be stricter
                pass

def _getString(node):
    s = u''
    child = node.children
    while child:
        if child.type == 'text':
            s += child.serialize('utf-8').decode('utf-8')
        child = child.next
    return s


def _node_is_text_only(node):
    yes = 1
    if node:
        child = node.children
        while child and child.isText():
            child = child.next
        if child and not child.isText():
            return 0
        else:
            return 1
    else:
        return 0
        

if __name__=='__main__':
    print getReleases()['gnome-2-20']
    
