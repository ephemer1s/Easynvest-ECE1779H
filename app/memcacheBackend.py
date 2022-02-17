import os
from app import memcache, memcacheStatistics, memcacheConfig, Stats, Stat
import datetime


def _cacheInsert(key, name):
    """Insert into cache

    Args:
        key (string): The key
        name (string): The filename
    """
    if key and name:
        memcache[key] = {'name': name, 'time': datetime.datetime.now()}


def getFromCache(key):
    """Get file name from memcache given a key. Calls DB on cache miss(TBD)

    Args:
        key (string): The key

    Returns:
        string: The file name
    """
    if key:
        if key not in memcache.keys():
            # cache missed, update statistics
            _updateStatsMiss()

            # Get name from database, insert to memcache
            _cacheInsert(getFromDB())

            return memcache[key]['name']
        else:
            # cache hit, update statistics
            _updateStatsHit()
            return memcache[key]['name']


def _updateStatsHit():
    memcacheStatistics.addStat(Stat(datetime.datetime.now(), 'hit'))
    memcacheStatistics.numOfRequestsServed += 1

    # (TBD)
    memcacheStatistics.totalSize = updateSize()
    memcacheStatistics.numOfItems = updateNumberOfItems()
    pass


def _updateStatsMiss():
    memcacheStatistics.addStat(Stat(datetime.datetime.now(), 'miss'))
    memcacheStatistics.numOfRequestsServed += 1

    # (TBD)
    memcacheStatistics.totalSize = updateSize()
    memcacheStatistics.numOfItems = updateNumberOfItems()
    pass


def cacheAdd(key, name):
    """(TBD) 
    API function for Adding a (key, filename) pair to memcache. There are 3 outcomes:
        1. Key DNE.
            We add the (key, filename) pair to memcache, 
            call DB (TBD), update stats (Cache miss) (Size)
        2. Key exists. 
            We replace the (key, filename) pair in memcache, 
            dropping (Deleting) the pair with the same key, 
            call DB (TBD), update stats (Cache hit) (Size)
        3. Key DNE, memcache full.
            Depending on replacement policy, either:
                a. Randomly drop one (key, filename) pair, see if memcache still too full
                    update stats (Cache miss) (Size)
                b. LRU: drop the one with the oldest timestamp in memcache, see if memcache still too full
                    update stats (Cache miss) (Size)

    Args:
        key (string): The key
        name (string): The filename
    """

    if not key or not name:
        print("Error: key or name missing!")
        return
    if key not in memcache.keys():
        # cache miss

        # Check if size is sufficient
        checkSize = True

        # ...(TBD)

        if checkSize:
            memcache[key] = {'name': name,
                             'timestamp': datetime.datetime.now()}

        else:
            # Check Replacement policy

            # ...(TBD)
            pass

        _updateStatsMiss()

    elif key in memcache.keys():
        memcache[key] = {'name': name, 'timestamp': datetime.datetime.now()}
        _updateStatsHit()
    pass


def clrCache():
    """Drop all key pairs in memcache
    Note that the file delete should be done in front end
    """
    memcache.clear()
    memcacheStatistics.totalSize = updateSize()
    memcacheStatistics.numOfItems = 0

    # update stats
    pass


def delCache(key):
    """Delete a key pair in memcache
    Note that the file delete should be done in front end
    """
    if key and key in memcache.keys():
        memcache.pop(key)
        # update stats
        memcacheStatistics.totalSize = updateSize()
        memcacheStatistics.numOfItems = memcacheStatistics.numOfItems - 1
    pass


def getFromDB():

    pass


def updateSize():
    return 0


def updateNumberOfItems():
    return 0
