import os
from backEnd import webapp, memcache, memcacheStatistics, memcacheConfig, Stats, Stat
import datetime
import random
from config import Config
from flask import request, jsonify, session
import shutil
from markupsafe import escape


def _clrCache(folderPath=Config.MEMCACHE_FOLDER):
    """Drop all key pairs in memcache
    Will have to delete all images from cacheImageFolder
    """

    for image in (folderPath):
        for filetype in Config.IMAGE_FORMAT:
            if image.endswith(filetype):
                os.remove(os.path.join(folderPath, image))

    memcache.clear()

    # update stats
    memcacheStatistics.totalSize = _updateSize(
        folderPath=Config.MEMCACHE_FOLDER)
    pass


def _delCache(key, folderPath=Config.MEMCACHE_FOLDER):
    """Delete a key pair in memcache

    """
    if key and key in memcache.keys():

        imageName = memcache[key]['name']
        os.remove(os.path.join(folderPath, imageName))

        memcache.pop(key)
        # update stats
        memcacheStatistics.totalSize = _updateSize()
    pass


def _getFromDB():

    pass


def _updateSize(folderPath='./cacheImageFolder'):

    # assign size
    size = 0

    for ele in os.scandir(folderPath):
        size += os.stat(ele).st_size  # In Bytes
    return size


def _getSize(imagePath='./images/random.jpg'):

    # assign size
    size = os.path.getsize(imagePath)  # In Bytes
    return size


def _cacheInsert(key, name):
    """Insert into cache

    Args:
        key (string): The key
        name (string): The filename
    """
    if key and name:
        memcache[key] = {'name': name, 'time': datetime.datetime.now()}


def _updateStatsHit():
    memcacheStatistics.addStat(Stat(datetime.datetime.now(), 'hit'))
    memcacheStatistics.numOfRequestsServed += 1

    # (TBD)
    memcacheStatistics.totalSize = _updateSize()
    pass


def _updateStatsMiss():
    memcacheStatistics.addStat(Stat(datetime.datetime.now(), 'miss'))
    memcacheStatistics.numOfRequestsServed += 1

    # (TBD)
    memcacheStatistics.totalSize = _updateSize()
    pass


@webapp.route('/put/<key>/<name>/<path>')
def PUT(key, name, path):
    """API function to set the key and value

    Args:
        key (string): key
        name (string): file name of the image, should include extensions
        path (string): file path for backend to copy

        [NOT USED] content (file): File Pointer? For the backEnd to copy from

    Returns:
        json:   "success": "true" or "false",
                "statusCode": 200 or 400,
                "message": What happened
    """

    if not key or not name:
        print("Error: key or name missing!")
        message = "Error: key or name missing!"
        return jsonify({"success": "false",
                        "statusCode": 400,
                        "message": message
                        })

    if not path:
        print("Error: Path missing!")
        message = "Error: Path missing!"
        return jsonify({"success": "false",
                        "statusCode": 400,
                        "message": message
                        })

    if key not in memcache.keys():
        # Check if size is sufficient
        checkSize = True

        if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:
            checkSize = False

        while (checkSize == False):
            # Check Replacement policy, LRU or Random Replacement

            if memcacheConfig['policy'] == "LRU":
                # delete the oldest

                # loop through memcache and check datetime, pop the oldest one
                oldestTimeStamp = min([d['timestamp']
                                       for d in memcache.values()])
                oldestKey = memcache.keys(
                )[memcache.values().index(oldestTimeStamp)]

                # delete the file in cacheImageFolder as well
                _delCache(oldestKey, folderPath=Config.MEMCACHE_FOLDER)

            elif memcacheConfig['policy'] == "Random":

                # delete a random one
                _delCache(random.choice([memcache.keys()]),
                          folderPath=Config.MEMCACHE_FOLDER)

            # Check if size is now sufficient

            if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:
                checkSize = False
            else:
                checkSize = True

        memcache[key] = {'name': name, 'timestamp': datetime.now()}

        # Copy file from path

        shutil.copy2(path, os.path.join(
            Config.MEMCACHE_FOLDER, memcache[key]['name']))

        message = "key \"" + escape(key) + "\" is now in memcache"
        return jsonify({"success": "true",
                        "statusCode": 200,
                        "message": message
                        })

    elif key in memcache.keys():
        # Should not happen, since frontEnd should invalidate first

        # Replace
        _delCache(key, folderPath=Config.MEMCACHE_FOLDER)

        # Check if size is sufficient
        checkSize = True

        if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:
            checkSize = False

        while (checkSize == False):
            # Check Replacement policy, LRU or Random Replacement

            if memcacheConfig['policy'] == "LRU":
                # delete the oldest

                # loop through memcache and check datetime, pop the oldest one
                oldestTimeStamp = min([d['timestamp']
                                       for d in memcache.values()])
                oldestKey = memcache.keys(
                )[memcache.values().index(oldestTimeStamp)]

                # delete the file in cacheImageFolder as well
                _delCache(oldestKey, folderPath=Config.MEMCACHE_FOLDER)

            elif memcacheConfig['policy'] == "Random":

                # delete a random one
                _delCache(random.choice([memcache.keys()]),
                          folderPath=Config.MEMCACHE_FOLDER)

            # Check if size is now sufficient

            if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:
                checkSize = False
            else:
                checkSize = True

        memcache[key] = {'name': name, 'timestamp': datetime.now()}

        # Copy file from path

        shutil.copy2(path, os.path.join(
            Config.MEMCACHE_FOLDER, memcache[key]['name']))

        message = "key \"" + key + "\" is now replaced"
        return jsonify({"success": "true",
                        "statusCode": 200,
                        "message": message
                        })

    message = "YOU SHOULD NOT BE HERE"
    return jsonify({"success": "false",
                    "statusCode": 400,
                    "message": message})


@ webapp.route('/get/<key>')
def GET(key):
    """API function to get the content associated with the key

    Args:
        key (string): Key

    Returns:
        json:   "cache": "hit" or "miss" or "",
                "filename",
                "filePath"
    """

    if key:
        if key not in memcache.keys():
            # cache missed, update statistics
            _updateStatsMiss()

            message = "cache miss; Please get file content from Local File System and call /backEnd/put/<key>/<name>/<path>"
            return jsonify({"cache": "miss",
                            "filename": "",
                            "filePath": "",
                            "message": message
                            })
        else:
            # cache hit, update statistics
            _updateStatsHit()
            message = "cache hit!"
            return jsonify({"cache": "hit",
                            "filename": memcache[key]['name'],
                            "filePath": os.path.join(Config.MEMCACHE_FOLDER, memcache[key]['name']),
                            "message": message
                            })

    message = "Usage: /get/<key>"
    return jsonify({"cache": "",
                    "filename": "",
                    "filePath": "",
                    "message": message
                    })


@ webapp.route('/clear')
def CLEAR():
    """API function for dropping all keys and values
    """
    _clrCache(folderPath=Config.MEMCACHE_FOLDER)


@ webapp.route('/invalidateKey/<key>')
def invalidateKey(key):
    """API function to drop a specific key (Should be called when uploading an image)

    Args:
        key (string): key to the dropped key
    """
    _delCache(key, folderPath=Config.MEMCACHE_FOLDER)
    pass


@ webapp.route('/refreshConfiguration')
def refreshConfiguration():
    """API Function call to read mem-cache related details from the database
    and reconfigure it with default values

    (TBD)
    """
    pass
