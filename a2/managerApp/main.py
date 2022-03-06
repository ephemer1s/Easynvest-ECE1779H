import base64
import managerApp
from managerApp.config import ConfigManager
import mysql.connector
from managerApp import webapp
from flask import json, render_template, url_for, request, g, flash, redirect, send_file, jsonify
from re import TEMPLATE
import http.client
import requests
import time
import threading

import os
TEMPLATE_DIR = os.path.abspath("./templates")
STATIC_DIR = os.path.abspath("./static")


@webapp.route('/')
def main():
    """Main Page

    Returns:
        html of Main Page
    """
    pass
