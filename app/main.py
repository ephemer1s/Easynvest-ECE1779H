from re import TEMPLATE


import os
TEMPLATE_DIR = os.path.abspath("./templates")
STATIC_DIR = os.path.abspath("./static")

from flask import json, render_template, url_for, request, g
from app import webapp, memcache



import mysql.connector
from app.config import db_config

def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])

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

#===================================Under Construction=============================================
@webapp.route('/')
def main():
    return render_template("index.html")


@webapp.route('/upload')
def upload():
    return render_template("main-old.html")  # TODO: need to adjust this html and corresponding get codes


@webapp.route('/browse')
def browse():
    pass


@webapp.route('/keylist')
# Display all keys in the database
def keylist():

    cnx = mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])

    cursor = cnx.cursor()
    query = "SELECT * FROM keylist"
    cursor.execute(query)
    view = render_template("keylist.html",title="Keylist", cursor=cursor)
    cnx.close()
    return view 


@webapp.route('/config')
def config():
    pass


@webapp.route('/status')
def status():
    pass
#===================================Under Construction=============================================

@webapp.route('/get',methods=['POST'])
def get():
    key = request.form.get('key')

    if key in memcache:
        value = memcache[key]
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

@webapp.route('/put',methods=['POST'])
def put():
    key = request.form.get('key')
    value = request.form.get('value')
    memcache[key] = value

    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response
