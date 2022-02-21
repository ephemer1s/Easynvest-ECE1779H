#!../venv/bin/python
# from app import webapp
# from app.main import main

from werkzeug.serving import run_simple  # werkzeug development server
# use to combine each Flask app into a larger one that is dispatched based on prefix
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from backEnd import webapp as backEnd
from frontEnd import webapp as frontEnd

backEnd.secret_key = "Secreeeeeeeeeeet"
frontEnd.secret_key = "UltraSecreeeeeeeeeeet"

applications = DispatcherMiddleware(frontEnd, {
    '/backEnd': backEnd
})

if __name__ == "__main__":
    """Two Flask instances are combine into a single object. Using "threaded = True", the function can call API within itself while dealing with user requests.
    """
    run_simple('0.0.0.0', 5000, applications,
               use_reloader=True,
               use_debugger=False,
               use_evalex=True,
               threaded=True)
