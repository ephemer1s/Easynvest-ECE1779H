from flask import Flask
from frontEnd.config import Config


webapp = Flask(__name__)
from frontEnd import main


@webapp.before_first_request
def _run_on_start():
    """
    App initialization, automatically run on start.
    """
    pass

