import pandas as pd
from datetime import datetime
from collections import deque
import threading
import queue
import sqlite3 as db

class DataStore:
    def __init__(self, maxlen=1000):
        self.connection = db.connect("databaseFile.db")
        self.cur = self.connection.cursor()
        self.data = {
            'time_stamp': deque(maxlen=maxlen),
            'speed': deque(maxlen=maxlen),
            'objects': deque(maxlen=maxlen),
            'area': deque(maxlen=maxlen)
        }
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.createTable()
    def createTable(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS storeHouse(
        time_stamp datetime,
        speed float,
        objects float,
        area float
        )""")
        self.connection.commit()

    def insertRow(self , speed, objects, area):
        curDate = datetime.now()
        self.cur.execute("INSERT INTO storeHouse VALUES (?, ?, ?, ?)", (curDate, speed, objects, area))
        self.connection.commit()

    def add_data(self, speed, objects, area):
        with self.lock:
            self.data['time_stamp'].append(datetime.now())
            self.data['speed'].append(int(speed))
            self.data['objects'].append(int(objects))
            self.data['area'].append(int(area))

        self.insertRow(speed, objects, area)

    def getLastRow(self):
        self.cur.execute("SELECT * FROM storeHouse ORDER BY time_stamp DESC LIMIT 1")
        return self.cur.fetchone()
    def getAllData(self):
        self.cur.execute("SELECT * FROM storeHouse ORDER BY time_stamp DESC")
        return self.cur.fetchall()
    def get_dataframe(self):
        with self.lock:
            return pd.DataFrame(self.data)

