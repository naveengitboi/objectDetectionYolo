import pandas as pd
import datetime
import sqlite3 as db

class DataStore:
    def __init__(self, make_table = True):
        self.connection = db.connect("data_file_2.db",check_same_thread=False)
        self.cur = self.connection.cursor()
        if make_table:
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
        curDate = datetime.datetime.now()
        self.cur.execute("INSERT INTO storeHouse VALUES (?, ?, ?, ?, ?)", (curDate, speed, objects, area, motor_class))
        self.connection.commit()

    def add_data(self, speed, objects, area, motor_class):
        self.insertRow(speed, objects, area, motor_class)

    def get_last_row(self):
        return pd.read_sql_query("SELECT * FROM storeHouse ORDER BY time_stamp DESC LIMIT ?", con=self.connection,
                                 params=[1])

    def get_all_data(self, motor_type = 'seg_belt'):
        return pd.read_sql_query("SELECT * FROM storeHouse WHERE motor_class LIKE ? ORDER BY time_stamp DESC", con=self.connection, params=[motor_type])

    def close(self):
        self.connection.commit()
        self.connection.close()

    def get_selected_data(self, startDate, endDate,  motor_type = 'seg_belt'):
        start_date = self._parse_date(startDate) or datetime.date.today()
        end_date = self._parse_date(endDate) or datetime.date.today()

        # Format dates for SQL query
        start_str = start_date.strftime('%Y-%m-%d 00:00:00')
        end_str = end_date.strftime('%Y-%m-%d 23:59:59')

        query = """
                    SELECT * 
                    FROM storeHouse 
                    WHERE motor_class LIKE ? AND time_stamp >= ? AND time_stamp <= ?
                """
        return pd.read_sql_query(query, con=self.connection, params=[motor_type, start_str, end_str])

    def group_by_data(self, grpBy, motor_type = 'seg_belt'):
        group_expr = {
            'Day': "DATE(time_stamp)",
            'Month': "STRFTIME('%Y-%m', time_stamp)",
            'Week': "STRFTIME('%Y-W%W', time_stamp)",
            'Year': "STRFTIME('%Y', time_stamp)",
            'Hour': "STRFTIME('%Y-%m-%d %H:00', time_stamp)",
            'Minute': "STRFTIME('%Y-%m-%d %H:%M', time_stamp)"
        }.get(grpBy)

        if not group_expr:
            raise ValueError("Invalid grouping period")

        query = f"""
            SELECT
                *,
                {group_expr} as time_period,
                AVG(speed) as avgSpeed,
                COUNT(*) as record_count
            FROM storeHouse
            WHERE motor_class LIKE ?
            GROUP BY time_period
            ORDER BY time_period
            """
        return pd.read_sql_query(query, self.connection, params=[motor_type])

    def _parse_date(self, date_str):
        """Helper method to parse date strings into date objects."""
        if not date_str:
            return None
        try:
            return datetime.datetime.strptime(str(date_str), "%Y-%m-%d").date()
        except ValueError:
            return None