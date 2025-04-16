import numpy as np
import datetime
import pandas as pd
import sqlite3 as db

def connectDb():
    connection = db.connect('dummy.db')
    print(connection)
    cursor = connection.cursor()
    return cursor, connection
data = {
    "timestamp": [],
    "speed": [],
    "objects": [],
    "area":[]
}

def addData(speed, area, objects):
    cursor, connection = connectDb()
    currDate = datetime.datetime.now()
    cursor.execute(f"""INSERT INTO database values({currDate}, {speed}, {area}, {objects})""")
    connection.commit()

addData(200.0,900,80)
addData(300,800,40)
addData(500,200,30)
addData(800,10,2)

def getFullData():
    cursor, connection = connectDb()
    cursor.execute("SELECT * FROM database")
    return pd.DataFrame(cursor.fetchall())


def getLastRow():
    cursor, connection = connectDb()
    lastQuery = """
            SELECT *
            FROM database
            LIMIT 1
        """
    cursor.execute(lastQuery)
    return pd.DataFrame(cursor.fetchone())



