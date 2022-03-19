import math, threading, time, base64
import http.client
from re import TEMPLATE
import requests
import mysql.connector
import boto3
from flask import json, render_template, url_for, request, g, flash, redirect, send_file, jsonify

# custom imports
import managerApp
from managerApp import webapp
from managerApp.config import ConfigManager
from botocore.exceptions import ClientError
import tools
from tools.awsS3 import S3_Class
from tools.awsEC2 import MemcacheEC2
from tools.awsCloudwatch import CloudwatchAPI
from tools.credential import ConfigAWS


import os
TEMPLATE_DIR = os.path.abspath("./templates")
STATIC_DIR = os.path.abspath("./static")

# Mode config for autoscaler. 0 = manual mode, 1 = auto mode.
AUTOSCALER_MODE = 1


def connect_to_database():
    return mysql.connector.connect(user=ConfigManager.db_config['user'],
                                   password=ConfigManager.db_config['password'],
                                   host=ConfigManager.db_config['host'],
                                   database=ConfigManager.db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.before_first_request
def _run_on_start():
    """Initialization when the flask app first startup. 
    """
    try:
        ec2_client = boto3.client('ec2',
                                  "us-east-1",
                                  aws_access_key_id=ConfigAWS.aws_access_key_id,
                                  aws_secret_access_key=ConfigAWS.aws_secret_access_key)
        call_obj = MemcacheEC2(ec2_client)

        call_obj.statelessRefresh()

        print("Memcache EC2 situation before start:")
        instanceIDs = call_obj.whoAreExisting()
        runningInstanceIDs = call_obj.whoAreRunning()
        print("Initializing Memcache...")

        # Check current memcache ec2 instance status and do initialization
        if not runningInstanceIDs:
            # Status 1: If no ec2 exist, create a new one
            if not instanceIDs:
                print("Initialization Status 1")
                call_obj.create_ec2_instance()
            # Status 2: If there are more than 1 ec2 exist but none of them are running, start 1 ec2 with the smallest number and terminate the rest
            elif len(instanceIDs) > 1:
                print("Initialization Status 2")
                call_obj.start_ec2_instance(call_obj.whoAreExisting()[0])
                for i in range(len(instanceIDs)-1):
                    call_obj.terminate_ec2_instance()
            # Status 3: If there is only 1 ec2 exists and is not running, just start it
            else:
                print("Initialization Status 3")
                call_obj.start_ec2_instance(call_obj.whoAreExisting()[0])
        else:
            shutdownInstanceNum = []    # Store  not running instance number
            for num in call_obj.whoAreExisting():
                if (num not in call_obj.whoAreRunning()):
                    shutdownInstanceNum.append(num)
            # Status 4: If there are some ec2 running with others shutdown, terminate all shutdown ec2 and keep the running one running
            if len(shutdownInstanceNum) > 0:
                print("Initialization Status 4")
                for num in shutdownInstanceNum:
                    call_obj.terminate_one_ec2_instance(num)
            # Status 5: If all the existing ec2 are running, just do nothing and keep going happily
            else:
                print("Initialization Status 5")

    except ClientError as e:
        print("AWS memcache initialization failed: ", e)

    # Thread for auto scaler starts
    autoScalerThreading = threading.Thread(target=autoScalerMonitor)
    autoScalerThreading.start()


@webapp.route('/')
def main():
    """Main Page

    Returns:
        html of Main Page
    """

    ec2_client = boto3.client('ec2',
                              "us-east-1",
                              aws_access_key_id=ConfigAWS.aws_access_key_id,
                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = MemcacheEC2(ec2_client)

    instanceAmount = len(call_obj.whoAreExisting())

    cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                  password=ConfigManager.db_config['password'],
                                  host=ConfigManager.db_config['host'],
                                  database=ConfigManager.db_config['database'])

    cursor = cnx.cursor()
    query = "SELECT itemTotalSize, itemNum, requestNum, missRate, hitRate FROM statistics WHERE id = 0"
    cursor.execute(query)
    memCacheStatistics = cursor.fetchall()

    view = render_template(
        "managerApp.html", instanceAmount=instanceAmount, cursor=memCacheStatistics)
    cnx.close()
    return view


@webapp.route('/replacePolicyUpdate', methods=['POST'])
def replacePolicyUpdate():
    """Update memcache replacement policy to Cloudwatch, and call memcache to refreshConfigurations

    Returns:
        Response message if updating successfully
    """

    capacityMB = request.form.get('capacityMB', "")
    replacePolicy = request.form.get('replacepolicy', "")

    # convert MB form capacity into B form
    capacityB = int(capacityMB) * 1048576

    # ATTENTION: Currently updating to the RDS databse. It should have been updating to Cloudwatch. Modify this part before deployment.
    cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                  password=ConfigManager.db_config['password'],
                                  host=ConfigManager.db_config['host'],
                                  database=ConfigManager.db_config['database'])

    cursor = cnx.cursor()
    cursor.execute("UPDATE configuration SET capacityB = %s, replacepolicy = %s WHERE id = 0",
                   (capacityB, replacePolicy,))
    cnx.commit()
    cnx.close()

    # please note to add /backEnd to the API call url
    # update on 3/16/13:00 : removed /backend from makeAPICall
    # status = makeAPI_Call("http://127.0.0.1:5001/refreshConfiguration" + "/" + str(capacityB) + "/" + str(replacepolicy), "get", 5)

    # v ----------------------------------------------------------------------------------- Ass 2 ----------------------------------------------------------------------------------- v
    ec2_client = boto3.client('ec2',
                              "us-east-1",
                              aws_access_key_id=ConfigAWS.aws_access_key_id,
                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = MemcacheEC2(ec2_client)

    ipList = call_obj.get_all_ip()

    for eachIP in ipList:
        # eachIP = '127.0.0.1'  # debug
        try:
            url = "http://" + eachIP + ":5001/refreshConfiguration" + \
                "/" + str(capacityB) + "/" + str(replacePolicy)
            print(url)
            returnDict = makeAPI_Call(url, "get", 5)
            print(returnDict)

        except requests.exceptions.RequestException as e:
            print("ERROR: ", e)
    # ^ ----------------------------------------------------------------------------------- Ass 2 ----------------------------------------------------------------------------------- ^

    # print(status)

    # # Need to notify frontend that memcachePool has updated
    # try:
    #     makeAPI_Call_Not_Json(
    #         "http://127.0.0.1:5000/memcachePoolUpdated/" + str(capacityB), "get", 5)

    # except requests.exceptions.RequestException as e:
    #     print("ERROR in managerApp: memcachePoolUpdated: ", e)

    response = webapp.response_class(
        response=json.dumps(
            "Memcache Replacement Policy Configs Update Successfully."),
        status=200,
        mimetype='application/json'
    )
    print(response)
    return response


@webapp.route('/poolSizeManualGrow', methods=['POST'])
def poolSizeManualGrow():
    """Manually grow memcache pool size by 1
    Call aws tools to create a ec2 instance

    Returns:
        Response message if creating successfully
    """
    ec2_client = boto3.client('ec2',
                              "us-east-1",
                              aws_access_key_id=ConfigAWS.aws_access_key_id,
                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = MemcacheEC2(ec2_client)

    if len(call_obj.whoAreExisting()) < 8:
        global AUTOSCALER_MODE
        AUTOSCALER_MODE = 0
        print("AutoScaler Mode: Manual")
        call_obj.create_ec2_instance()
        response = webapp.response_class(
            response=json.dumps("Memcache Pool Size Growing Successfully."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    else:
        response = webapp.response_class(
            response=json.dumps(
                "Memcache Pool Size Has Already Reached Its Maximum. Growing Failed."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    return response


@webapp.route('/poolSizeManualShrink', methods=['POST'])
def poolSizeManualShrink():
    """Manually shrink memcache pool size by 1
    Call aws tools to create a ec2 instance

    Returns:
        Response message if shrinking successfully
    """
    ec2_client = boto3.client('ec2',
                              "us-east-1",
                              aws_access_key_id=ConfigAWS.aws_access_key_id,
                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = MemcacheEC2(ec2_client)

    if len(call_obj.whoAreRunning()) > 1:
        global AUTOSCALER_MODE
        AUTOSCALER_MODE = 0
        print("AutoScaler Mode: Manual")
        call_obj.terminate_ec2_instance()
        publicIPUpdater()
        response = webapp.response_class(
            response=json.dumps("Memcache Pool Size Shrinking Successfully."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    else:
        response = webapp.response_class(
            response=json.dumps(
                "Memcache Pool Size Has Already Reached Its Minimum. Shrinking Failed."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    return response


@webapp.route('/poolResizeAuto', methods=['POST'])
def poolResizeAuto():
    """Configure a simple auto-scaling policy to resize the memcache pool size
    API function to automatically resize memcache pool size with preset cloudwatch threshold
    by calling awsEC2 API to start or terminate EC2 memcache instance

    Returns:
        Response message if resizing successfully
    """
    maxMissRate = float(request.form.get('maxMissRate', ""))/100
    minMissRate = float(request.form.get('minMissRate', ""))/100
    poolExpandRatio = request.form.get('poolExpandRatio', "")
    poolShrinkRatio = request.form.get('poolShrinkRatio', "")

    if maxMissRate > minMissRate+0.01:
        # ATTENTION: Currently updating to the RDS database. It should have been updating to Cloudwatch. Modify this part before deployment.
        cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                      password=ConfigManager.db_config['password'],
                                      host=ConfigManager.db_config['host'],
                                      database=ConfigManager.db_config['database'])

        cursor = cnx.cursor()
        cursor.execute("UPDATE autoscalerconfigs SET maxMissRate = %s, minMissRate = %s, poolExpandRatio = %s, poolShrinkRatio = %s WHERE id = 0",
                       (maxMissRate, minMissRate, poolExpandRatio, poolShrinkRatio))
        cnx.commit()
        cnx.close()

        print("AutoScaler Mode: Auto")
        global AUTOSCALER_MODE
        AUTOSCALER_MODE = 1

        response = webapp.response_class(
            response=json.dumps(
                "Memcache Auto Scaler Configs Update Successfully."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    elif maxMissRate == minMissRate+0.01:
        response = webapp.response_class(
            response=json.dumps(
                "Error: The difference between Max and Min Miss Rate is too SMALL. Updating failed."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    else:
        response = webapp.response_class(
            response=json.dumps(
                "Error: Max Miss Rate must be LARGER than Min Miss Rate. Updating failed."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    return response


def autoScalerMonitor():
    """Loops every 60s, call autoScaler()
    """
    while True:
        autoScaler()
        publicIPUpdater()
        time.sleep(60)  # It could be something like 5s when testing


def publicIPUpdater():
    """Update current running memcache EC2 public ip to frontEnd update_IP_List API
    """
    # ATTENTION: Please remember to add publicIPUpdater() after every terminate_ec2_instance(), otherwise potential bug could exist
    ec2_client = boto3.client('ec2',
                              "us-east-1",
                              aws_access_key_id=ConfigAWS.aws_access_key_id,
                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = MemcacheEC2(ec2_client)

    ipList = call_obj.get_all_ip()

    # Tell memcache what their ids are:

    returnDict = {}
    id = 0
    for eachIP in ipList:

        try:
            returnDict = makeAPI_Call_Not_Json("http://" + eachIP + ":5001/updateIndex" +
                                               "/" + str(id), "get", 5)
            id = id + 1

        except requests.exceptions.RequestException as e:
            print("ERROR: ", e)
            id = id + 1

    ipStr = ''

    for i in range(len(ipList)):
        if i == 0:
            ipStr += ipList[i]
        else:
            ipStr += '_'
            ipStr += ipList[i]

    # ipStr = '127.0.0.1'  # debug

    dataDict = {"IPLIST": ipStr}

    # ATTENTION: Only uncomment this makeAPI_Call code to make this function actually work when frontEnd app is running
    makeAPI_Call_Not_Json(
        "http://127.0.0.1:5000/updateIPList", "post", 5, _data=dataDict)


def autoScaler():
    """Automatically resizes the memcache pool based on configuration values set by the managerApp
    """
    global AUTOSCALER_MODE
    # Status 0 Manual Mode : AUTOSCALER thread is still running but stay hands off
    if AUTOSCALER_MODE == 0:
        print("AutoScaler Status 0: Manual")
    else:
        # IMPORTANT: It takes about 30s to create or terminate an instance completely

        # ATTENTION: Currently acquiring statics from RDS databse. It should have been fetched from Cloudwatch. Modify this part before deployment.
        cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                      password=ConfigManager.db_config['password'],
                                      host=ConfigManager.db_config['host'],
                                      database=ConfigManager.db_config['database'])
        cursor = cnx.cursor()

        ######## Old code for fetching missrate using SQL cursor
        # cursor.execute("SELECT missRate FROM statistics WHERE id = 0")

        # memcacheStatics = cursor.fetchall()
        # missRate = memcacheStatics[0][0]
        ######## New code for fetching missrate from cloudwatch by @Haocheng
        # Check this @ Haozhe
        # TODO: modify this index list.
        index_list = None
        index_list = [str(i) for i in index_list]
        cloudwatch = CloudwatchAPI(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
        response = cloudwatch.getCacheMissRate(response, index_list, intervals=60, periods=5)
        print([str(i['Datapoints']) for i in response]) # test prints
        missrate = cloudwatch.getLastMeanMissRate(response)
        

        cursor.execute(
            "SELECT maxMissRate, minMissRate, poolExpandRatio, poolShrinkRatio FROM autoscalerconfigs WHERE id = 0")
        autoScalerConfigs = cursor.fetchall()
        maxMissRate = autoScalerConfigs[0][0]
        minMissRate = autoScalerConfigs[0][1]
        poolExpandRatio = autoScalerConfigs[0][2]
        poolShrinkRatio = autoScalerConfigs[0][3]

        cnx.close()

        # Check memcache EC2 status
        ec2_client = boto3.client('ec2',
                                  "us-east-1",
                                  aws_access_key_id=ConfigAWS.aws_access_key_id,
                                  aws_secret_access_key=ConfigAWS.aws_secret_access_key)
        call_obj = MemcacheEC2(ec2_client)

        curInstanceNum = len(call_obj.whoAreExisting())

        # Status 2 Miss Rate too low : shrinking pool size
        if missRate <= minMissRate:
            # When shrinking, floor targetInstanceNum
            # e.g: 8 * 0.95 = 7.6 → 7
            targetInstanceNum = int(float(curInstanceNum) * poolShrinkRatio)

            # Never shrnking pool size to 0
            if targetInstanceNum < 1:
                targetInstanceNum = 1

            # Set miss rate to a safe value temporarily otherwise autoscaler may stuck
            # ATTENTION: Currently acquiring statics from RDS databse. It should have been fetched from Cloudwatch. Modify this part before deployment.
            cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                          password=ConfigManager.db_config['password'],
                                          host=ConfigManager.db_config['host'],
                                          database=ConfigManager.db_config['database'])

            cursor = cnx.cursor()
            cursor.execute("UPDATE statistics SET missRate = %s, hitRate = %s WHERE id = 0",
                           (minMissRate+0.01, 0.99-minMissRate,))
            cnx.commit()
            cnx.close()

            # ATTENTION: Currently we have to terminate instance one by one, since a second terminate call would not actually work if there is already an instance under termination
            # Maybe we could consider using _terminate_ec2_instance() to terminate multiple instances at the same time
            for i in range(curInstanceNum - targetInstanceNum):
                print("AutoScaler Status 2: Shrinking...")
                call_obj.terminate_ec2_instance()

                publicIPUpdater()

                time.sleep(3)

        # Status 3 Miss Rate too high : growing pool size
        elif missRate >= maxMissRate:
            # When growing, ceiling targetInstanceNum
            # e.g: 1 * 1.2 = 1.2 → 2
            targetInstanceNum = math.ceil(
                float(curInstanceNum) * poolExpandRatio)

            # Never growing pool size more than 8
            if targetInstanceNum > 8:
                targetInstanceNum = 8

            # Set miss rate to a safe value temporarily otherwise autoscaler may stuck
            # ATTENTION: Currently acquiring statics from RDS databse. It should have been fetched from Cloudwatch. Modify this part before deployment.
            cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                          password=ConfigManager.db_config['password'],
                                          host=ConfigManager.db_config['host'],
                                          database=ConfigManager.db_config['database'])

            cursor = cnx.cursor()
            cursor.execute("UPDATE statistics SET missRate = %s, hitRate = %s WHERE id = 0",
                           (maxMissRate-0.01, 1.01-maxMissRate,))
            cnx.commit()
            cnx.close()

            for i in range(targetInstanceNum - curInstanceNum):
                print("AutoScaler Status 3: Growing...")
                call_obj.create_ec2_instance()
                time.sleep(3)

        # Status 1 Miss Rate Steady : hands off and keep monitoring
        else:
            print("AutoScaler Status 1: Steady")


# Under Construction
@webapp.route('/clearDatabase', methods=['POST'])
def clearDatabase():
    """Delete image path data stored in the database and all image files stored in S3

    Returns:
        Response message if deleting successfully
    """

    # Delete all the rows of image path info in database
    cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                  password=ConfigManager.db_config['password'],
                                  host=ConfigManager.db_config['host'],
                                  database=ConfigManager.db_config['database'])

    cursor = cnx.cursor()
    cursor.execute("DELETE FROM keylist")
    cnx.commit()
    cnx.close()

    # Delete all the image file in S3
    # ATTENTION: Require S3 clear code here

    s3_client = boto3.client('s3',
                             "us-east-1",
                             aws_access_key_id=ConfigAWS.aws_access_key_id,
                             aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = S3_Class(s3_client)
    call_obj.delete_all()

    # Under Construction

    response = webapp.response_class(
        response=json.dumps(
            "Database and S3 data delete successfully."),
        status=200,
        mimetype='application/json'
    )
    print(response)
    return response

# Under Construction


@webapp.route('/clearMemcache', methods=['POST'])
def clearMemcache():
    """Clear the content of all memcache nodes in the pool

    Returns:
        Response message if clearing successfully
    """

    ec2_client = boto3.client('ec2',
                              "us-east-1",
                              aws_access_key_id=ConfigAWS.aws_access_key_id,
                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = MemcacheEC2(ec2_client)

    ipList = call_obj.get_all_ip()

    for eachIP in ipList:
        api_url = "http://" + eachIP + ":5001/clear"
        returnDict = makeAPI_Call(api_url, "get", 10)

        if returnDict["message"] == 'OK':
            print("Memcache File Clear: " + eachIP)

    response = webapp.response_class(
        response=json.dumps(
            "Memcache data delete successfully."),
        status=200,
        mimetype='application/json'
    )
    print(response)
    return response


@webapp.route('/home')
def backHome():
    """Home Page: Call to go back to home page "/"

    Returns:
        html of Home Page
    """
    return render_template("managerApp.html")


@webapp.route('/wakeUp')
def wakeUp():
    """called from frontend on startup to get memcache working
    """
    print("Manager App is up! UwU")
    return jsonify({"success": "true",
                    "statusCode": 200})


def makeAPI_Call(api_url: str, method: str, _timeout: int, _data={}):
    """Helper function to call an API.

    Args:
        api_url (str): URL to the API function
        method (str): get, post, delete, or put
        _timeout (int): (in seconds) how long should the front end wait for a response

    Returns:
        <?>: response
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1",
               "DNT": "1", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate"}
    method = method.lower()
    if method == "get":
        r = requests.get(api_url, timeout=_timeout, headers=headers)
    if method == "post":
        r = requests.post(api_url, data=_data,
                          timeout=_timeout, headers=headers)
    if method == "delete":
        r = requests.delete(api_url, timeout=_timeout, headers=headers)
    if method == "put":
        r = requests.put(api_url, timeout=_timeout, headers=headers)

    json_acceptable_string = r.json()

    return json_acceptable_string


def makeAPI_Call_Not_Json(api_url: str, method: str, _timeout: int, _data={}):
    """Helper function to call an API.

    Args:
        api_url (str): URL to the API function
        method (str): get, post, delete, or put
        _timeout (int): (in seconds) how long should the front end wait for a response

    Returns:
        <?>: response
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1",
               "DNT": "1", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate"}
    method = method.lower()
    if method == "get":
        r = requests.get(api_url, timeout=_timeout, headers=headers)
    if method == "post":
        r = requests.post(api_url, data=_data,
                          timeout=_timeout, headers=headers)
    if method == "delete":
        r = requests.delete(api_url, timeout=_timeout, headers=headers)
    if method == "put":
        r = requests.put(api_url, timeout=_timeout, headers=headers)

    return r
