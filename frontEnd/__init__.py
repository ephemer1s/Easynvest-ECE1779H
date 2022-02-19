from flask import Flask
import datetime

webapp = Flask(__name__)

global old_memcache

old_memcache = {}
try:
    from frontEnd import main
except ImportError:
    print("wtf no Front End?")
