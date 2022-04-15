import json, os
import requests
import flask, boto3, twelvedata, jinja2, numpy
from flask import url_for

def current_handler(event, context):
    return index_handler(event, context)

def lambda_handler(event, context):
    r = requests.get('https://www.google.com/')
    if r.status_code == 200:
        print(r)
        return 'Successful'
    else:
        print(r)
        return 'Unsuccessful'
        
def version_handler(event, context):
    print(flask.__version__)
    print(boto3.__version__)
    print(twelvedata.__version__)
    print(numpy.__version__)
    return 'Successful'
    
    
def render_without_request(template_name, **template_vars):
    """
    Usage is the same as flask.render_template:

    render_without_request('my_template.html', var1='foo', var2='bar')
    """
    templateLoader = jinja2.FileSystemLoader(searchpath="./template")
    env = jinja2.Environment(loader=templateLoader)

    template = env.get_template(template_name)
    return template.render(**template_vars)


def html_handler(event, context):
    return {
        "statusCode": 200,
        "headers": {'Content-Type': 'text/html'},   #it really works by Hector Duran!
        "body": render_without_request('index.html')
    }
    
    
def render_template_without_flask(template_name, **template_vars):
    """
    Usage is the same as flask.render_template:
    render_template('my_template.html', var1='foo', var2='bar')
    """
    if os.path.exists('./frontEnd/templates'):
        template_path = './frontEnd/templates'
    else:
        template_path = './templates'

    templateLoader = jinja2.FileSystemLoader(searchpath=template_path)
    env = jinja2.Environment(loader=templateLoader)

    template = env.get_template(template_name)
    return template.render(**template_vars)


def wrap(body):
    '''
    Wrap the rendered template in a http response with status code 200
    '''
    return {
        "statusCode": 200,
        "headers": {'Content-Type': 'text/html'},
        "body": body
    }


# @webapp.route('/home')
def index_handler(event, context):
    """Home Page: Call to go back to main page "/"

    Returns:
        html of Main Page
    """
    return wrap(render_template_without_flask("index.html"))