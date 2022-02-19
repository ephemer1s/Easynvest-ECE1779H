import os
from backEnd import webapp, memcache, memcacheStatistics, memcacheConfig, Stats, Stat
import datetime
import random
from backEnd.config import Config
from flask import request, jsonify, session
import shutil
import json
from markupsafe import escape


def _clrCache(folderPath=Config.MEMCACHE_FOLDER):
    """Drop all key pairs in memcache
    Will have to delete all images from cacheImageFolder
    """

    for image in os.listdir(folderPath):
        print("Trying to delete ", image)
        for filetype in Config.IMAGE_FORMAT:
            if image.endswith(filetype):
                print("Deleting ", image)
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
        return "Deleted"
    memcacheStatistics.totalSize = _updateSize()
    return "Did not delete"


def _getFromDB():

    pass


def _updateSize(folderPath=Config.MEMCACHE_FOLDER):

    # assign size
    size = 0

    for ele in os.scandir(folderPath):
        size += os.stat(ele).st_size  # In Bytes

    print("Capacity: ", size, "/", memcacheConfig['capacity'])
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

    memcacheStatistics.totalSize = _updateSize()
    pass


def _updateStatsMiss():
    memcacheStatistics.addStat(Stat(datetime.datetime.now(), 'miss'))
    memcacheStatistics.numOfRequestsServed += 1

    memcacheStatistics.totalSize = _updateSize()
    pass


@webapp.route('/put/<key>/<name>/<path:path>')
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
    if not os.path.isfile(path):
        print("Error: File is missing!")
        message = "Error: File is missing!"
        return jsonify({"success": "false",
                        "statusCode": 400,
                        "message": message
                        })

    memcacheStatistics.totalSize = _updateSize()

    keyAlreadyExist = False

    if key in memcache.keys():
        # Should not happen, since frontEnd should invalidate first

        # Replace
        _delCache(key, folderPath=Config.MEMCACHE_FOLDER)
        keyAlreadyExist = True

    if key not in memcache.keys():
        # Check if size is sufficient
        checkSize = True

        if _getSize(path) > memcacheConfig['capacity']:
            # Someone is crazy enough to upload an image that is larger than the capacity allowed. We cant save it!
            print("Error: File size larger than capacity allowed!")
            message = "Error: File size larger than capacity allowed!"
            return jsonify({"success": "false",
                            "statusCode": 400,
                            "message": message
                            })

        if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:

            if(not memcache):
                # memcache is empty but folder is not. Calling _clrcache()
                _clrCache(folderPath=Config.MEMCACHE_FOLDER)
            else:
                checkSize = False

        while (checkSize == False):
            # Check Replacement policy, LRU or Random Replacement

            if(not memcache):
                # memcache is empty but folder is not. Calling _clrcache()
                _clrCache(folderPath=Config.MEMCACHE_FOLDER)

            if memcacheConfig['policy'] == "LRU":
                # delete the oldest

                # loop through memcache and check datetime, pop the oldest one
                oldestTimeStamp = min([d['timestamp']
                                       for d in memcache.values()])

                oldestKey = ""
                for keys in memcache.keys():
                    if memcache[keys]['timestamp'] == oldestTimeStamp:
                        oldestKey = keys
                # delete the file in cacheImageFolder as well
                if(oldestKey):
                    _delCache(oldestKey, folderPath=Config.MEMCACHE_FOLDER)
                else:
                    print("how can this happen to me?")

            elif memcacheConfig['policy'] == "Random":

                # delete a random one
                _delCache(random.choice(list(memcache)),
                          folderPath=Config.MEMCACHE_FOLDER)

            # Check if size is now sufficient

            if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:
                checkSize = False
            else:
                checkSize = True

        memcache[key] = {'name': name, 'timestamp': datetime.datetime.now()}

        # Copy file from path

        shutil.copy2(path, os.path.join(
            Config.MEMCACHE_FOLDER, memcache[key]['name']))
        memcacheStatistics.totalSize = _updateSize()

        if keyAlreadyExist:
            message = "key " + escape(key) + " is now REPLACED."
            return jsonify({"success": "true",
                            "statusCode": 200,
                            "message": message
                            })
        else:
            message = "key " + escape(key) + " is now in memcache."
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
    message = "OK"
    return jsonify({"statusCode": 200,
                    "message": message})


@ webapp.route('/invalidateKey/<key>')
def invalidateKey(key):
    """API function to drop a specific key (Should be called when uploading an image)

    Args:
        key (string): key to the dropped key
    """
    returnValue = _delCache(key, folderPath=Config.MEMCACHE_FOLDER)

    if returnValue == "Did not delete":
        response = webapp.response_class(
            response=json.dumps("Failed to delete"),
            status=200,
            mimetype='application/json'
        )
        print(response)
        return response

    elif returnValue == "Deleted":

        response = webapp.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )
        print(response)
        return response


@ webapp.route('/refreshConfiguration')
def refreshConfiguration():
    """API Function call to read mem-cache related details from the database
    and reconfigure it with default values

    (TBD)
    """
    message = "Refreshed"
    return jsonify({"success": "true",
                    "statusCode": 200,
                    "message": message})


@webapp.route('/')
def main():
    # to get the current working directory
    directory = os.getcwd()

    print(directory)
    message = directory
    return jsonify({"success": "true",
                    "statusCode": 200,
                    "message": message})


@webapp.route('/putkey/<key>/<name>')
def PUTkey(key, name):
    """debug function to set the key and value (No Path)

    Args:
        key (string): key
        name (string): file name of the image, should include extensions

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

    if key not in memcache.keys():
        memcache[key] = {'name': name, 'timestamp': datetime.datetime.now()}

        message = "key " + escape(key) + " is now in memcache"
        return jsonify({"success": "true",
                        "statusCode": 200,
                        "message": escape(message)
                        })

    elif key in memcache.keys():
        # Should not happen, since frontEnd should invalidate first

        # Replace
        memcache.pop(key)

        memcache[key] = {'name': name, 'timestamp': datetime.datetime.now()}

        message = "key " + key + " is now replaced"
        return jsonify({"success": "true",
                        "statusCode": 200,
                        "message": message
                        })

    message = "YOU SHOULD NOT BE HERE"
    return jsonify({"success": "false",
                    "statusCode": 400,
                    "message": message})


@webapp.route('/init')
def init():
    """Please call this when booting up the frontend
    """

    if not os.path.isdir(Config.MEMCACHE_FOLDER):
        try:
            os.mkdir(Config.MEMCACHE_FOLDER)
        except OSError as error:
            print(error)
    _clrCache(folderPath=Config.MEMCACHE_FOLDER)

    message = "Cache cleared and ready to roll"
    return jsonify({"success": "true",
                    "statusCode": 200,
                    "message": message})


@webapp.route('/listKeys')
def listKeys():
    """debug: List all keys
    """
    listOfKeys = []

    for keys in memcache.keys():
        listOfKeys.append(keys)

    message = ','.join([str(elem) for elem in listOfKeys])
    return jsonify({"success": "true",
                    "statusCode": 200,
                    "message": message})


@webapp.route('/statistic')
def statistic():
    """debug: Give statistics to frontEnd to store in database every 5s
    """
    missrate, hitrate = memcacheStatistics.getTenMinStats()

    returnArray = [len(memcache), memcacheStatistics.totalSize,
                   memcacheStatistics.numOfRequestsServed, missrate, hitrate]

    return jsonify({"success": "true",
                    "statusCode": 200,
                    "message": returnArray})
