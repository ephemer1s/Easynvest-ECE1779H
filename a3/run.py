from flask import Flask
# from werkzeug.serving import run_simple
# from werkzeug.middleware.dispatcher import DispatcherMiddleware

from frontEnd import webapp


if __name__ == "__main__":
    """Two Flask instances are combine into a single object. Using "threaded = True", the function can call API within itself while dealing with user requests.
    """
    webapp.run(debug=True)