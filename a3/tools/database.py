'''
database.py
Author : ephemer1s, haozhe0302
Description : 
    tool functions for database connection, partly moved and modified from A1/frontEnd/main.py
'''


import mysql.connector
from flask import g

try:
    from tools.credential import ConfigDB
except:
    from credential import ConfigDB

class Database():

    def connect_to_database(self):
        return mysql.connector.connect(user=ConfigDB.user,
                                    password=ConfigDB.password,
                                    host=ConfigDB.host,
                                    database=ConfigDB.database,)


    def get_db(self):
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = self.connect_to_database()
        return db


    # @webapp.teardown_appcontext
    def teardown_db(self):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()