from flask import Flask

webapp = Flask(__name__)

try:
    from tools import awsEC2

except Exception as e:
    print("tools/__init__.py: Failed: from tools import awsEC2")
    print("Error: ", e)
