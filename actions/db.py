# db.py (create this as a helper file)
import pymysql

def get_db_connection():
    return pymysql.connect(
        host="srv1631.hstgr.io",        # e.g. "srv123.hostinger.com"
        username="u611944498_sangkaychatbot",
        password="Sangkay2025",
        database="u611944498_sangkayDB",
        cursorclass=pymysql.cursors.DictCursor  # returns results as dicts
    )