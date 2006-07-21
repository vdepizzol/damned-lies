# -*- encoding: utf-8 -*-

import defaults

from sqlobject import * 
import datetime

import os
if not os.access(defaults.scratchdir, os.X_OK | os.R_OK | os.W_OK):
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

class ArchivedStatistics(SQLObject):
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

    Messages = MultipleJoin('ArchivedInformation')


class Information(SQLObject):
    _cacheValue = False

    Statistics = ForeignKey('Statistics', notNone=True)
    Type = EnumCol(enumValues=['info', 'warn', 'error']) # priority of a stats message
    Description = UnicodeCol()


class ArchivedInformation(SQLObject):
    _cacheValue = False

    Statistics = ForeignKey('ArchivedStatistics', notNone=True)
    Type = EnumCol(enumValues=['info', 'warn', 'error']) # priority of a stats message
    Description = UnicodeCol()

def init():
    Statistics.createTable(ifNotExists = True)
    ArchivedStatistics.createTable(ifNotExists = True)
    Information.createTable(ifNotExists = True)
    ArchivedInformation.createTable(ifNotExists = True)

if __name__ == "__main__":
    init()
