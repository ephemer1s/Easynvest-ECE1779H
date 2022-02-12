import os
from app import d_memcache, l_memcacheStatistics, d_memcacheConfig
import datetime
from app import Stat
from app import Stats

# Backend Cache API

# Insert file name, key and insert time to dict


def cacheInsert(key, name):
    if key and name:
        d_memcache[key] = {'name': name, 'time': datetime.datetime.now()}


def getFromCache(key):
    if key:
        if key not in d_memcache.keys():
            # cache missed, update statistics
            updateStatsMiss()

            # Get name from database, insert to memcache
            cacheInsert(getFromDB())

            return d_memcache[key]['name']
        else:
            # cache hit, update statistics
            updateStatsHit()
            return d_memcache[key]['name']


def updateStatsHit():
    l_memcacheStatistics.addStat(Stat(datetime.datetime.now(), 'hit'))
    pass


def updateStatsMiss():
    l_memcacheStatistics.addStat(Stat(datetime.datetime.now(), 'miss'))
    pass


def cacheAdd(key, name):
    if not key or not name:
        print("Error: key or name missing!")
        return

    pass


def getFromDB():

    pass
