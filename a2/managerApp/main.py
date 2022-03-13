import base64
import managerApp
from managerApp.config import ConfigManager
import mysql.connector
from managerApp import webapp

import boto3
from botocore.exceptions import ClientError
import tools
from tools.awsEC2 import MemcacheEC2
from tools.credential import ConfigAWS

from flask import json, render_template, url_for, request, g, flash, redirect, send_file, jsonify
from re import TEMPLATE
import http.client
import math
import requests
import time
import threading

import os
TEMPLATE_DIR = os.path.abspath("./templates")
STATIC_DIR = os.path.abspath("./static")

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
            if len(shutdownInstanceNum)>0:
                print("Initialization Status 4")
                for num in shutdownInstanceNum:
                    # ATTENTION: Currently _terminate_ec2_instance() method are not available for external call, which would cause a warning
                    # If _terminate_ec2_instance could not be available, apply a similar rule as status 2
                    # Status 4 is not functionable right now
                    _terminate_ec2_instance(num)
            # Status 5: If all the existing ec2 are running, just do nothing and keep going happily
            else:
                print("Initialization Status 5")

    except ClientError as e:
        print("AWS memcache initialization failed: ", e)

    # Thread for auto scaler starts
    autoScalerThreading = threading.Thread(target=autoScalerUpdater)
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

    view = render_template("managerApp.html", instanceAmount = instanceAmount, cursor=memCacheStatistics)
    cnx.close()
    return view


@webapp.route('/replacePolicyUpdate', methods=['POST'])
def replacePolicyUpdate():
    """Update memcache replacement policy to Cloudwatch, and call memcache to refreshConfigurations

    Returns:
        Response message if updating successfully
    """

    capacityMB = request.form.get('capacityMB', "")
    replacepolicy = request.form.get('replacepolicy', "")

    # convert MB form capacity into B form
    capacityB = int(capacityMB) * 1048576

    # ATTENTION: Currently updating to the RDS databse. It should have been updating to Cloudwatch. Modify this part before deployment.
    cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                  password=ConfigManager.db_config['password'],
                                  host=ConfigManager.db_config['host'],
                                  database=ConfigManager.db_config['database'])

    cursor = cnx.cursor()
    cursor.execute("UPDATE configuration SET capacityB = %s, replacepolicy = %s WHERE id = 0",
                   (capacityB, replacepolicy,))
    cnx.commit()
    cnx.close()

    # please note to add /backEnd to the API call url
    status = makeAPI_Call("http://127.0.0.1:5001/backEnd/refreshConfiguration" + "/" + str(capacityB) + "/" + str(replacepolicy), "get", 5)

    print(status)

    response = webapp.response_class(
        response=json.dumps("Memcache Replacement Policy Configs Update Successfully."),
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

    if len(call_obj.whoAreExisting())<8:
        call_obj.create_ec2_instance()
        response = webapp.response_class(
            response=json.dumps("Memcache Pool Size Growing Successfully."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    else:
        response = webapp.response_class(
            response=json.dumps("Memcache Pool Size Has Already Reached Its Maximum. Growing Failed."),
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

    if len(call_obj.whoAreRunning())>1:
        call_obj.terminate_ec2_instance()
        response = webapp.response_class(
            response=json.dumps("Memcache Pool Size Shrinking Successfully."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    else:
        response = webapp.response_class(
            response=json.dumps("Memcache Pool Size Has Already Reached Its Minimum. Shrinking Failed."),
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
        # ATTENTION: Currently updating to the RDS databse. It should have been updating to Cloudwatch. Modify this part before deployment.
        cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                    password=ConfigManager.db_config['password'],
                                    host=ConfigManager.db_config['host'],
                                    database=ConfigManager.db_config['database'])

        cursor = cnx.cursor()
        cursor.execute("UPDATE autoscalerconfigs SET maxMissRate = %s, minMissRate = %s, poolExpandRatio = %s, poolShrinkRatio = %s WHERE id = 0",
                    (maxMissRate, minMissRate, poolExpandRatio, poolShrinkRatio))
        cnx.commit()
        cnx.close()

        response = webapp.response_class(
            response=json.dumps("Memcache Auto Scaler Configs Update Successfully."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    elif maxMissRate == minMissRate+0.01:
        response = webapp.response_class(
            response=json.dumps("Error: The difference between Max and Min Miss Rate is too SMALL. Updating failed."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    else:
        response = webapp.response_class(
            response=json.dumps("Error: Max Miss Rate must be LARGER than Min Miss Rate. Updating failed."),
            status=200,
            mimetype='application/json'
        )
        print(response)
    return response


def autoScalerUpdater():
    """Loops every 5s, call autoScaler()
    """
    while True:
        autoScaler()
        time.sleep(5)


def autoScaler():
    """Automatically resizes the memcache pool based on configuration values set by the managerApp
    """

    # IMPORTANT: It takes about 30s to create or terminate an instance

    # ATTENTION: Currently acquiring statics from RDS databse. It should have been fetched from Cloudwatch. Modify this part before deployment.
    cnx = mysql.connector.connect(user=ConfigManager.db_config['user'],
                                    password=ConfigManager.db_config['password'],
                                    host=ConfigManager.db_config['host'],
                                    database=ConfigManager.db_config['database'])

    cursor = cnx.cursor()
    cursor.execute("SELECT missRate FROM statistics WHERE id = 0")

    memcacheStatics = cursor.fetchall()
    missRate = memcacheStatics[0][0]

    cursor.execute("SELECT maxMissRate, minMissRate, poolExpandRatio, poolShrinkRatio FROM autoscalerconfigs WHERE id = 0")
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

    # Status 1 Miss Rate too low : shrinking pool size
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
            print("AutoScaler Status 1: Shrinking...")
            call_obj.terminate_ec2_instance()
            time.sleep(30)

    # Status 2 Miss Rate too high : growing pool size
    elif missRate >= maxMissRate:
        # When growing, ceiling targetInstanceNum
        # e.g: 1 * 1.2 = 1.2 → 2
        targetInstanceNum = math.ceil(float(curInstanceNum) * poolExpandRatio)

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
            print("AutoScaler Status 2: Growing...")
            call_obj.create_ec2_instance()
            time.sleep(5)

    # Status 0 Miss Rate Steady : hands off and keep monitoring
    else:
        print("AutoScaler Status 0: Steady")


# Under Construction
@webapp.route('/clearDatabase', methods=['POST'])
def clearDatabase():
    """Delete image data stored on the database and all image files stored on S3

    Returns:
        Response message if deleting successfully
    """
    pass

# Under Construction
@webapp.route('/clearMemcache', methods=['POST'])
def clearMemcache():
    """Clear the content of all memcache nodes in the pool

    Returns:
        Response message if clearing successfully
    """
    pass


@webapp.route('/home')
def backHome():
    """Home Page: Call to go back to home page "/"

    Returns:
        html of Home Page
    """
    return render_template("managerApp.html")


def makeAPI_Call(api_url: str, method: str, _timeout: int):
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
        r = requests.post(api_url, timeout=_timeout, headers=headers)
    if method == "delete":
        r = requests.delete(api_url, timeout=_timeout, headers=headers)
    if method == "put":
        r = requests.put(api_url, timeout=_timeout, headers=headers)

    json_acceptable_string = r.json()

    return json_acceptable_string