import base64
from flask import render_template, url_for, request
from app import webapp, memcache, memcacheStatistics, memcacheConfig
from flask import json


@webapp.route('/')
def main():
    return render_template("main.html")


@webapp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@webapp.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@webapp.route('/get', methods=['POST'])
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


@webapp.route('/put', methods=['POST'])
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
