import base64
import frontEnd
from frontEnd.config import Config
import mysql.connector
from frontEnd import webapp, old_memcache
from flask import json, render_template, url_for, request, g, flash
from re import TEMPLATE

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
    if file.filename == '':
        flash('No selected file')
        # return redirect(request.url)
    if file:
        print(type(file))
        upload_folder = webapp.config['UPLOAD_FOLDER']
        if not os.path.isdir(upload_folder):
            os.mkdir(upload_folder)
        filename = os.path.join(upload_folder, file.filename)
        file.save(filename)
        # return redirect(url_for('download_file', name=file.filename))
    old_memcache[key] = file
    if file is not None:
        base64_data = base64.b64encode(file)
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )
    print(response)
    return response
