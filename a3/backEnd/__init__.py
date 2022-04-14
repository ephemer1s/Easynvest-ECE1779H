from flask import Flask
from frontEnd import main

webapp = Flask(__name__)

@webapp.before_first_request
def _run_on_start():
    """
    App initialization, automatically run on start.
    """
    pass