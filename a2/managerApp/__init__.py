from flask import Flask
import datetime

from managerApp.config import ConfigManager

webapp = Flask(__name__)

# global old_memcache

# old_memcache = {}
try:
    from managerApp import main
except Exception as e:
    print("wtf no Manager App?")
    print("Error: ", e)

# webapp.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
