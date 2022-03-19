from flask import Flask
import datetime

webapp = Flask(__name__)

try:
    from tools import awsEC2

except Exception as e:
    print("wtf no AWS tools?")
    print("Error: ", e)
