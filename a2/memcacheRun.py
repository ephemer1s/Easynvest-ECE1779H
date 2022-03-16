#!../venv/bin/python
# from app import webapp
# from app.main import main
import time, os

from werkzeug.serving import run_simple  # werkzeug development server
# use to combine each Flask app into a larger one that is dispatched based on prefix
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from managerApp import webapp as managerApp
from backEnd import webapp as backEnd
from frontEnd import webapp as frontEnd

managerApp.secret_key = "Secreeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeet"
backEnd.secret_key = "Secreeeeeeeeeeet"
frontEnd.secret_key = "UltraSecreeeeeeeeeeet"

application = DispatcherMiddleware({'/backEnd': backEnd})

if __name__ == "__main__":
    """Using "threaded = True", the function can call API within itself while dealing with user requests.
    """
    if not os.path.exists('./logs'):
        os.mkdir('./logs')

    run_simple('0.0.0.0', 5001, application,
               use_reloader=True,
               use_debugger=True,
               use_evalex=True,
               threaded=True)
    with open("./logs/memcache.log", 'a') as f:
        f.write(str(time.time()) + "Memcache has loaded!\n")