import os
import datetime
import random
import json
import base64
import time
import threading
import shutil
from markupsafe import escape
import mysql.connector
import boto3
from flask import request, jsonify, session

from backEnd import webapp, memcache, memcacheStatistics, memcacheConfig, Stats, Stat
from backEnd.config import Config
from tools.awsCloudwatch import CloudwatchAPI
from tools.credential import ConfigAWS


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


@webapp.route('/put/<key>/<name>', methods=['POST'])
def PUT(key, name):
    """API function to set the key and value

    Args:
        key (string): key
        name (string): file name of the image, should include extensions
        # path (string): file path for backend to copy

        content (file): Base64 image data

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

    content = request.form.get('imgContent')

    if not content:
        print("Error: content missing!")
        message = "Error: content missing!"
        return jsonify({"success": "false",
                        "statusCode": 400,
                        "message": message
                        })

    # Save base64 to a "Temp" location:

    tempFilePath = Config.TEMP_FOLDER + "/" + name

    with open(tempFilePath, "wb") as tempImage:
        tempImage.write(base64.b64decode(content))

    path = tempFilePath

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

            for image in os.listdir(Config.TEMP_FOLDER):
                print("Trying to delete ", image)
            for filetype in Config.IMAGE_FORMAT:
                if image.endswith(filetype):
                    print("Deleting ", image)
                    os.remove(os.path.join(Config.TEMP_FOLDER, image))

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

        # # Copy file from path

        shutil.copy2(path, os.path.join(
            Config.MEMCACHE_FOLDER, memcache[key]['name']))

        for image in os.listdir(Config.TEMP_FOLDER):
            print("Trying to delete ", image)
        for filetype in Config.IMAGE_FORMAT:
            if image.endswith(filetype):
                print("Deleting ", image)
                os.remove(os.path.join(Config.TEMP_FOLDER, image))

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

# @webapp.route('/put/<key>/<name>/<path:path>')
# def PUT(key, name, path):
#     """API function to set the key and value

#     Args:
#         key (string): key
#         name (string): file name of the image, should include extensions
#         path (string): file path for backend to copy

#         [NOT USED] content (file): File Pointer? For the backEnd to copy from

#     Returns:
#         json:   "success": "true" or "false",
#                 "statusCode": 200 or 400,
#                 "message": What happened
#     """

#     if not key or not name:
#         print("Error: key or name missing!")
#         message = "Error: key or name missing!"
#         return jsonify({"success": "false",
#                         "statusCode": 400,
#                         "message": message
#                         })

#     if not path:
#         print("Error: Path missing!")
#         message = "Error: Path missing!"
#         return jsonify({"success": "false",
#                         "statusCode": 400,
#                         "message": message
#                         })
#     if not os.path.isfile(path):
#         print("Error: File is missing!")
#         message = "Error: File is missing!"
#         return jsonify({"success": "false",
#                         "statusCode": 400,
#                         "message": message
#                         })

#     memcacheStatistics.totalSize = _updateSize()

#     keyAlreadyExist = False

#     if key in memcache.keys():
#         # Should not happen, since frontEnd should invalidate first

#         # Replace
#         _delCache(key, folderPath=Config.MEMCACHE_FOLDER)
#         keyAlreadyExist = True

#     if key not in memcache.keys():
#         # Check if size is sufficient
#         checkSize = True

#         if _getSize(path) > memcacheConfig['capacity']:
#             # Someone is crazy enough to upload an image that is larger than the capacity allowed. We cant save it!
#             print("Error: File size larger than capacity allowed!")
#             message = "Error: File size larger than capacity allowed!"
#             return jsonify({"success": "false",
#                             "statusCode": 400,
#                             "message": message
#                             })

#         if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:

#             if(not memcache):
#                 # memcache is empty but folder is not. Calling _clrcache()
#                 _clrCache(folderPath=Config.MEMCACHE_FOLDER)
#             else:
#                 checkSize = False

#         while (checkSize == False):
#             # Check Replacement policy, LRU or Random Replacement

#             if(not memcache):
#                 # memcache is empty but folder is not. Calling _clrcache()
#                 _clrCache(folderPath=Config.MEMCACHE_FOLDER)

#             if memcacheConfig['policy'] == "LRU":
#                 # delete the oldest

#                 # loop through memcache and check datetime, pop the oldest one
#                 oldestTimeStamp = min([d['timestamp']
#                                        for d in memcache.values()])

#                 oldestKey = ""
#                 for keys in memcache.keys():
#                     if memcache[keys]['timestamp'] == oldestTimeStamp:
#                         oldestKey = keys
#                 # delete the file in cacheImageFolder as well
#                 if(oldestKey):
#                     _delCache(oldestKey, folderPath=Config.MEMCACHE_FOLDER)
#                 else:
#                     print("how can this happen to me?")

#             elif memcacheConfig['policy'] == "Random":

#                 # delete a random one
#                 _delCache(random.choice(list(memcache)),
#                           folderPath=Config.MEMCACHE_FOLDER)

#             # Check if size is now sufficient

#             if memcacheStatistics.totalSize + _getSize(path) > memcacheConfig['capacity']:
#                 checkSize = False
#             else:
#                 checkSize = True

#         memcache[key] = {'name': name, 'timestamp': datetime.datetime.now()}

#         # Copy file from path

#         shutil.copy2(path, os.path.join(
#             Config.MEMCACHE_FOLDER, memcache[key]['name']))
#         memcacheStatistics.totalSize = _updateSize()

#         if keyAlreadyExist:
#             message = "key " + escape(key) + " is now REPLACED."
#             return jsonify({"success": "true",
#                             "statusCode": 200,
#                             "message": message
#                             })
#         else:
#             message = "key " + escape(key) + " is now in memcache."
#             return jsonify({"success": "true",
#                             "statusCode": 200,
#                             "message": message
#                             })

#     message = "YOU SHOULD NOT BE HERE"
#     return jsonify({"success": "false",
#                     "statusCode": 400,
#                     "message": message})


@ webapp.route('/get/<key>')
def GET(key):
    """API function to get the content associated with the key

    Args:
        key (string): Key

    Returns:
        json:   "cache": "hit" or "miss" or "",
                "filename",
                "filePath",
                "message",
                "content" (Base 64)
    """

    if key:
        if key not in memcache.keys():
            # cache missed, update statistics
            _updateStatsMiss()

            message = "cache miss; Please get file content from Local File System and call /backEnd/put/<key>/<name>/<path>"
            return jsonify({"cache": "miss",
                            "filename": "",
                            "filePath": "",
                            "message": message,
                            "content": ""
                            })
        else:
            # cache hit, update statistics
            _updateStatsHit()
            message = "cache hit!"
            filepath = os.path.join(
                Config.MEMCACHE_FOLDER, memcache[key]['name'])
            filepath = filepath.replace('\\', '/')

            image = open(filepath, 'rb')
            image_Binary = image.read()
            imageBase64Encode = base64.b64encode(image_Binary)

            return jsonify({"cache": "hit",
                            "filename": memcache[key]['name'],
                            "filePath": filepath,
                            "message": message,
                            "content": imageBase64Encode.decode()
                            })

    message = "Usage: /get/<key>"
    return jsonify({"cache": "",
                    "filename": "",
                    "filePath": "",
                    "message": message,
                    "content": ""
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


# @ webapp.route('/refreshConfiguration/<capacity>/<policy>')
# def refreshConfiguration(capacity, policy):
#     """API Function call to read mem-cache related details from the database
#     and reconfigure it with default values
#     """

#     cnx = mysql.connector.connect(user=Config.db_config['user'],
#                                   password=Config.db_config['password'],
#                                   host=Config.db_config['host'],
#                                   database=Config.db_config['database'])

#     cursor = cnx.cursor()
#     query = "SELECT capacityB, replacepolicy FROM configuration WHERE id = 0"
#     cursor.execute(query)
#     cnx.close()

#     configuration = cursor.fetchall()

#     returnjson = jsonify({})
#     # Sql may fail. In that case abandon the change.
#     configSource = ""
#     if not configuration:
#         print("Failed to update config; SQL failed. Using values passed from frontEnd instead.")

#         memcacheConfig['capacity'] = int(capacity)

#         memcacheConfig['policy'] = "LRU" if policy == 1 else "Random"

#         configSource = "Failed to update config; SQL failed. Using values passed from frontEnd instead."

#     else:
#         print("Using Sql config data.")
#         configSource = "Using Sql config data."
#         print(configuration, configuration[0][0], configuration[0][1])

#         memcacheConfig['capacity'] = configuration[0][0]

#         memcacheConfig['policy'] = "LRU" if configuration[0][1] == 1 else "Random"

#     # Need to check if current Capacity is still enough

#     checkSize = True

#     if memcacheStatistics.totalSize > memcacheConfig['capacity']:

#         if(not memcache):
#             # memcache is empty but folder is not. Calling _clrcache()
#             _clrCache(folderPath=Config.MEMCACHE_FOLDER)
#         else:
#             checkSize = False

#     while (checkSize == False):
#         # Check Replacement policy, LRU or Random Replacement

#         if(not memcache):
#             # memcache is empty but folder is not. Calling _clrcache()
#             _clrCache(folderPath=Config.MEMCACHE_FOLDER)

#         if memcacheConfig['policy'] == "LRU":
#             # delete the oldest

#             # loop through memcache and check datetime, pop the oldest one
#             oldestTimeStamp = min([d['timestamp']
#                                    for d in memcache.values()])

#             oldestKey = ""
#             for keys in memcache.keys():
#                 if memcache[keys]['timestamp'] == oldestTimeStamp:
#                     oldestKey = keys
#             # delete the file in cacheImageFolder as well
#             if(oldestKey):
#                 _delCache(oldestKey, folderPath=Config.MEMCACHE_FOLDER)
#             else:
#                 print("how can this happen to me?")

#         elif memcacheConfig['policy'] == "Random":

#             # delete a random one
#             _delCache(random.choice(list(memcache)),
#                       folderPath=Config.MEMCACHE_FOLDER)

#         # Check if size is now sufficient

#         if memcacheStatistics.totalSize > memcacheConfig['capacity']:
#             checkSize = False
#         else:
#             checkSize = True

#     message = "Updated: " + \
#         str(memcacheConfig['capacity']) + \
#         ", " + str(memcacheConfig["policy"])
#     returnjson = jsonify({"success": "true",
#                           "statusCode": 200,
#                           "configSource": configSource,
#                           "message": message})
#     return returnjson


@ webapp.route('/refreshConfiguration/<capacity>/<policy>')
def refreshConfigurationManagerApp(capacity, policy):
    """API Function call to read mem-cache related details from the managerApp
    and reconfigure it
    """

    memcacheConfig['capacity'] = int(capacity)

    memcacheConfig['policy'] = "LRU" if policy == "1" else "Random"

    # Need to check if current Capacity is still enough

    checkSize = True

    if memcacheStatistics.totalSize > memcacheConfig['capacity']:

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

        if memcacheStatistics.totalSize > memcacheConfig['capacity']:
            checkSize = False
        else:
            checkSize = True

    message = "Updated: " + \
        str(memcacheConfig['capacity']) + \
        ", " + str(memcacheConfig["policy"])
    returnjson = jsonify({"success": "true",
                          "statusCode": 200,
                          "configSource": "managerApp",
                          "message": message})
    return returnjson


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

    if not os.path.isdir(Config.TEMP_FOLDER):
        try:
            os.mkdir(Config.TEMP_FOLDER)
        except OSError as error:
            print(error)
    _clrCache(folderPath=Config.TEMP_FOLDER)

    message = "Cache cleared and ready to roll"
    return jsonify({"success": "true",
                    "statusCode": 200,
                    "message": message})


@webapp.before_first_request
def _run_on_start():
    init()
    refreshConfigurationManagerApp(1000000, 'LRU')

    # start thread to update to cloudwatch every 5s.
    x = threading.Thread(target=cloudWatchUpdateMonitor)
    x.start()

    y = threading.Thread(target=databaseUpdateMonitor)
    y.start()


def cloudWatchUpdateMonitor():
    """_summary_ call cloudWatchUpdate() every 5s.
    """
    while True:
        cloudWatchUpdate()
        time.sleep(5)


def databaseUpdateMonitor():
    """_summary_ call databaseUpdate() every 60s.
    """
    while True:
        databaseUpdate()
        time.sleep(60)   # It should have been 60s. Set to 3s for testing.


def databaseUpdate():
    """ Update this memcache statistics log to database for ManagerApp charts to use
    """
    index, missRate, hitRate, totalNumOfRequests, numOfItemsInCache, totalSize, totalRequestsInAMin, currentTime = memcacheStatistics.getOneMinStats()
    # totalSize in bytes

    if index >= 0:  # Since index is set as -1 initially, you could set index != 99 or sth like that when testing
        cnx = mysql.connector.connect(user=Config.db_config['user'],
                                      password=Config.db_config['password'],
                                      host=Config.db_config['host'],
                                      database=Config.db_config['database'])

        cursor = cnx.cursor()

        # Insert new log into database
        cursor.execute("INSERT INTO memcachestatlog VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (index, currentTime, missRate, hitRate, totalRequestsInAMin, numOfItemsInCache, totalSize, ))
        cnx.commit()

        # Delete old memcache log of more than 30 min ago in database
        # I hate mysql. It makes things much harder :-(
        cursor.execute(
            "SELECT memcacheIndex, MIN(currentTime) FROM memcachestatlog GROUP BY memcacheIndex HAVING COUNT(currentTime) >= 31")
        oldestLog = cursor.fetchall()
        if oldestLog:
            oldestLogIndex = oldestLog[0][0]
            oldestLogTime = oldestLog[0][1]
            cursor.execute("DELETE FROM memcachestatlog WHERE memcacheIndex = %s AND currentTime = %s",
                           (oldestLogIndex, oldestLogTime, ))
            cnx.commit()
        cnx.close()

        print("Memcache Log Update to DB Successfully: ", index, " ", currentTime)
    pass


def cloudWatchUpdate():
    """ Give statistics to frontEnd to store in cloudWatch every 5s
    """
    # index, missRate, hitRate, totalNumOfRequests, numOfItemsInCache, totalSize, totalRequestsInAMin, currentTime = memcacheStatistics.getOneMinStats()
    index, missRate, _, _, _, _, _, _ = memcacheStatistics.getOneMinStats()
    # index, missRate, _, _, _, _, _ = memcacheStatistics.get5SecStats()

    # TODO: Can we get 5s stats here?
    # Call boto3 cloudwatch @Haocheng
    cloudwatch = CloudwatchAPI(
        ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
    response = cloudwatch.putCacheMissRate(missRate, str(index))
    print('Missrate Pushed to Cloudwatch : ' + str(response))
    return response


@webapp.route('/updateIndex/<id>')
def updateIndex(id):
    """Update id
    """

    memcacheStatistics.index = int(id)

    return jsonify({"success": "true",
                    "statusCode": 200})


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
    hitrate, missrate = memcacheStatistics.getTenMinStats()

    returnArray = [len(memcache), format((float(memcacheStatistics.totalSize)/1048576), '.3f'),
                   memcacheStatistics.numOfRequestsServed, format(missrate*100, '.3f'), format(hitrate*100, '.3f')]

    return jsonify({"success": "true",
                    "statusCode": 200,
                    "message": returnArray})
