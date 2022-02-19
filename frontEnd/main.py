import base64
import frontEnd
from frontEnd.config import Config
import mysql.connector
from frontEnd import webapp, old_memcache
from flask import json, render_template, url_for, request, g, flash, redirect
from re import TEMPLATE
import http.client
import requests
import time
import threading

import os
TEMPLATE_DIR = os.path.abspath("./templates")
STATIC_DIR = os.path.abspath("./static")


def connect_to_database():
    return mysql.connector.connect(user=Config.db_config['user'],
                                   password=Config.db_config['password'],
                                   host=Config.db_config['host'],
                                   database=Config.db_config['database'])


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

# ===================================Under Construction=============================================


@webapp.before_first_request
def _run_on_start():
    makeAPI_Call(
        "http://127.0.0.1:5000/backEnd/init", "get", 5)
    makeAPI_Call(
        "http://127.0.0.1:5000/backEnd/refreshConfiguration", "get", 5)
    x = threading.Thread(target=backEndUpdater)
    x.start()


def backEndUpdater():
    while True:
        updater()
        time.sleep(5)


def updater():
    json_dict = makeAPI_Call(
        "http://127.0.0.1:5000/backEnd/statistic", "get", 3)

    # statsDict = json.loads(json_acceptable_string)
    statsList = [-1, -1, -1, 0.0, 0.0]
    if (json_dict['success'] == 'true'):
        statsList = json_dict['message']
    print("Stats List: ", statsList)

    # Code to upload to database @ HaoZhe

    # ...

    pass


@webapp.route('/')
def main():
    return render_template("index.html")


@webapp.route('/upload')
def upload():
    # TODO: need to adjust this html and corresponding get codes
    return render_template("upload.html")


@webapp.route('/browse')
def browse():
    return render_template("browse.html")


@webapp.route('/keylist')
# Display all keys in the database
def keylist():

    cnx = mysql.connector.connect(user=Config.db_config['user'],
                                  password=Config.db_config['password'],
                                  host=Config.db_config['host'],
                                  database=Config.db_config['database'])

    cursor = cnx.cursor()
    query = "SELECT keyID, path FROM keylist"
    cursor.execute(query)
    view = render_template("keylist.html", title="Key List", cursor=cursor)
    cnx.close()
    return view


@webapp.route('/config')
def config():
    pass


@webapp.route('/status')
def status():
    pass
# ===================================Under Construction=============================================


@webapp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@webapp.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@webapp.route('/get', methods=['POST'])
def get():
    key = request.form.get('key')

    if key in old_memcache:
        value = old_memcache[key]
        response = webapp.response_class(
            response=json.dumps(value),
            status=200,
            mimetype='application/json'
        )
    else:
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response


@webapp.route('/put', methods=['POST'])
def put():
    key = request.form.get('key')
    file = request.files['file']
    print(key, file)

    if file.filename == '':  # Not working for some reason
        flash('No selected file')
        # return redirect("upload.html")

    # Go on database to find if key exist already. If it does, find path, drop

    uploadedFile = False
    if file:
        print(type(file))
        upload_folder = webapp.config['UPLOAD_FOLDER']
        if not os.path.isdir(upload_folder):
            os.mkdir(upload_folder)
        filename = os.path.join(upload_folder, file.filename)

        # Check if filename already exists in folder
        fileExists = True
        currentFileName = file.filename
        while (fileExists):
            if not os.path.isfile(filename):
                fileExists = False
            else:
                split_tup = os.path.splitext(currentFileName)
                currentFileName = split_tup[0] + "(copy)" + split_tup[1]
                filename = os.path.join(
                    upload_folder, currentFileName)

        file.save(filename)
        # return redirect(url_for('download_file', name=file.filename))
        uploadedFile = True

    old_memcache[key] = file

    if file is not None:
        # base64_data = base64.b64encode(file)
        pass
    if uploadedFile:
        # Call backEnd to invalidateKey
        api_url = "http://127.0.0.1:5000/backEnd/invalidateKey/" + key

        json_acceptable_string = makeAPI_Call(api_url, "get", 5)

    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )
    print(response)
    return response


def makeAPI_Call(api_url: str, method: str, _timeout: int):
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

    print("Here is response: ", json_acceptable_string)
    return json_acceptable_string
