from flask import Flask
import datetime

from frontEnd.config import Config

webapp = Flask(__name__)

# global old_memcache

# old_memcache = {}
try:
    from frontEnd import main
except Exception as e:
    print("wtf no Front End? ")
    print("Error: ", e)

webapp.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
