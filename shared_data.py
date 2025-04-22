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
        self.createTable()
    def createTable(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS storeHouse(
        time_stamp datetime,
        speed float,
        objects float,
        area float,
        motor_class varchar(50)
        )""")
        self.connection.commit()

    def insertRow(self , speed, objects, area, motor_class):
        curDate = datetime.now()
        self.cur.execute("INSERT INTO storeHouse VALUES (?, ?, ?, ?, ?)", (curDate, speed, objects, area, motor_class))
        self.connection.commit()

    def add_data(self, speed, objects, area, motor_class):
        self.insertRow(speed, objects, area, motor_class)
