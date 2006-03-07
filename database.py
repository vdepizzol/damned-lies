# -*- encoding: utf-8 -*-

import defaults

from sqlobject import * 
import datetime

import os
if not os.stat(defaults.scratchdir):
    os.makedirs(defaults.scratchdir)

conn = connectionForURI(defaults.database_connection)
__connection__ = conn


class Statistics(SQLObject):
    _cacheValue = False

    Module = UnicodeCol()
    Type = EnumCol(enumValues=['doc', 'ui']) # whether this is about a document or UI translation
    Domain = UnicodeCol()
    Branch = UnicodeCol()
    Language = StringCol() #ForeignKey('Language', notNone=False)
    Date = DateTimeCol(default=datetime.datetime.now)
    Translated = IntCol(default=0)
    Fuzzy = IntCol(default=0)
    Untranslated = IntCol(default=0)

    Messages = MultipleJoin('Information')


class Information(SQLObject):
    _cacheValue = False

    Statistics = ForeignKey('Statistics', notNone=True)
    Type = EnumCol(enumValues=['info', 'warn', 'error']) # priority of a stats message
    Description = UnicodeCol()

class Language(SQLObject):
    _cacheValue = True
    
    Code = StringCol(alternateID=True)
    Name = UnicodeCol()

def init():
    Statistics.createTable(ifNotExists = True)
    Information.createTable(ifNotExists = True)


    # Initialise language table
    Language.createTable(ifNotExists = True)
    import xml.dom.minidom
    dom = xml.dom.minidom.parse('/usr/share/xml/iso-codes/iso_639.xml')
    
    langs = dom.getElementsByTagName("iso_639_entry")
    for lang in langs:
        code = lang.getAttribute("iso_639_1_code")
        name = lang.getAttribute("name")

        if code and name and not Language.selectBy(Code=code).count():
            print u"%s: %s" % (code,name)
            try:
                newlang = Language(Code=code, Name=name)
            except:
                pass
    

if __name__ == "__main__":
    init()
