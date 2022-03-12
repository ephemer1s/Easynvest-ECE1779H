import base64
import managerApp
from managerApp.config import ConfigManager
import mysql.connector
from managerApp import webapp

# import error: awsEC2 not imported?
import tools
from tools import awsEC2
from tools.awsEC2 import MemcacheEC2

from flask import json, render_template, url_for, request, g, flash, redirect, send_file, jsonify
from re import TEMPLATE
import http.client
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

# Under Construction
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

    except ClientError as e:
        print("AWS tools client configuration error: ", e)
        

@webapp.route('/')
def main():
    """Main Page

    Returns:
        html of Main Page
    """
    return render_template("managerApp.html")

# Under Construction
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

    # ATTENTION: Currently updating to the RDS databse. It should have been updating to Cloudwatch. Modify this part before deploying.
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

# Under Construction
@webapp.route('/poolResizeManual', methods=['POST'])
def poolResizeManual():
    """Manually resize the memcache pool size by 1 betweeen 1 ~ 8
    Manually resize memcache pool size by calling awsEC2 API to start or terminate EC2 memcache instance

    Returns:
        Response message if resizing successfully
    """
    # Get a form from managerApp html to determin whether to grow or shrink the pool
    # Manual mode button still under construction. Need a feedback to the web user
    # CaLL aws tools API to start or terminate EC2 memcache
    # Return a response message to the user

    # Test Code

    call_obj.get_live_ec2_instance_id()
    call_obj.statelessRefresh()

    input("Press Enter to continue...")

    call_obj.create_ec2_instance()
    input("Press Enter to continue...")
    call_obj.get_live_ec2_instance_id()
    call_obj.get_live_ec2_running_instance_id()



    pass

# Under Construction
@webapp.route('/poolResizeAuto', methods=['POST']) 
def poolResizeAuto():
    """Configure a simple auto-scaling policy to resize the memcache pool size
    API function to automatically resize memcache pool size with preset cloudwatch threshold
    by calling awsEC2 API to start or terminate EC2 memcache instance

    Returns:
        Response message if resizing successfully
    """
    pass

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