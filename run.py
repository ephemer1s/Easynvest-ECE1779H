#!../venv/bin/python
from app import webapp
from app.main import main

if __name__ == "__main__":
    webapp.run('0.0.0.0',5001,debug=True)


