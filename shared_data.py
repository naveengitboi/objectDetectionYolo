import pandas as pd
import datetime
import sqlite3 as db


class DataStore:
    def __init__(self, make_table=True):
        self.connection = db.connect("data_file_2.db", check_same_thread=False)
        self.cur = self.connection.cursor()
        if make_table:
            self.createTables()  # Changed from createTable to createTables

    def createTables(self):
        """Create both tables if they don't exist"""
        # Main motor data table
        self.cur.execute("""CREATE TABLE IF NOT EXISTS storeHouse(
            time_stamp datetime,
            speed float,
            objects float,
            area float,
            motor_class varchar(50)
        """)

        # New load data table
        self.cur.execute("""CREATE TABLE IF NOT EXISTS load_data(
            time_stamp datetime,
            load_type varchar(50),
            weight float,
            status varchar(20) DEFAULT 'normal'
        """)

        self.connection.commit()

    def insertRow(self, speed, objects, area, motor_class):
        curDate = datetime.datetime.now()
        self.cur.execute("INSERT INTO storeHouse VALUES (?, ?, ?, ?, ?)",
                         (curDate, speed, objects, area, motor_class))
        self.connection.commit()

    def insertLoadData(self, load_type, weight, status="normal"):
        """Insert a new load measurement into the database"""
        curDate = datetime.datetime.now()
        self.cur.execute("INSERT INTO load_data VALUES (?, ?, ?, ?)",
                         (curDate, load_type, weight, status))
        self.connection.commit()

    def add_data(self, speed, objects, area, motor_class):
        self.insertRow(speed, objects, area, motor_class)

    def add_load_data(self, load_type, weight, status="normal"):
        """Add load data with optional status (normal/error/calibration)"""
        self.insertLoadData(load_type, weight, status)

    def get_last_row(self):
        return pd.read_sql_query("SELECT * FROM storeHouse ORDER BY time_stamp DESC LIMIT ?",
                                 con=self.connection, params=[1])

    def get_last_load(self):
        """Get the most recent load measurement"""
        return pd.read_sql_query("SELECT * FROM load_data ORDER BY time_stamp DESC LIMIT ?",
                                 con=self.connection, params=[1])

    def get_all_data(self, motor_type='seg_belt'):
        return pd.read_sql_query("SELECT * FROM storeHouse WHERE motor_class LIKE ? ORDER BY time_stamp DESC",
                                 con=self.connection, params=[motor_type])

    def get_all_load_data(self, load_type=None):
        """Get all load data, optionally filtered by type"""
        if load_type:
            return pd.read_sql_query("SELECT * FROM load_data WHERE load_type = ? ORDER BY time_stamp DESC",
                                     con=self.connection, params=[load_type])
        return pd.read_sql_query("SELECT * FROM load_data ORDER BY time_stamp DESC",
                                 con=self.connection)

    def close(self):
        self.connection.commit()
        self.connection.close()

    def get_selected_data(self, startDate, endDate, motor_type='seg_belt'):
        start_date = self._parse_date(startDate) or datetime.date.today()
        end_date = self._parse_date(endDate) or datetime.date.today()

        start_str = start_date.strftime('%Y-%m-%d 00:00:00')
        end_str = end_date.strftime('%Y-%m-%d 23:59:59')

        query = """
            SELECT * 
            FROM storeHouse 
            WHERE motor_class LIKE ? AND time_stamp >= ? AND time_stamp <= ?
        """
        return pd.read_sql_query(query, con=self.connection,
                                 params=[motor_type, start_str, end_str])

    def get_selected_load_data(self, startDate, endDate, load_type=None):
        """Get load data within a date range, optionally filtered by type"""
        start_date = self._parse_date(startDate) or datetime.date.today()
        end_date = self._parse_date(endDate) or datetime.date.today()

        start_str = start_date.strftime('%Y-%m-%d 00:00:00')
        end_str = end_date.strftime('%Y-%m-%d 23:59:59')

        if load_type:
            query = """
                SELECT * 
                FROM load_data 
                WHERE load_type = ? AND time_stamp >= ? AND time_stamp <= ?
            """
            return pd.read_sql_query(query, con=self.connection,
                                     params=[load_type, start_str, end_str])
        else:
            query = """
                SELECT * 
                FROM load_data 
                WHERE time_stamp >= ? AND time_stamp <= ?
            """
            return pd.read_sql_query(query, con=self.connection,
                                     params=[start_str, end_str])

    def group_by_data(self, grpBy, motor_type='seg_belt'):
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

    def group_load_data(self, grpBy, load_type=None):
        """Group load data by time period"""
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

        if load_type:
            query = f"""
                SELECT
                    {group_expr} as time_period,
                    AVG(weight) as avg_weight,
                    COUNT(*) as record_count
                FROM load_data
                WHERE load_type = ?
                GROUP BY time_period
                ORDER BY time_period
            """
            return pd.read_sql_query(query, self.connection, params=[load_type])
        else:
            query = f"""
                SELECT
                    {group_expr} as time_period,
                    load_type,
                    AVG(weight) as avg_weight,
                    COUNT(*) as record_count
                FROM load_data
                GROUP BY time_period, load_type
                ORDER BY time_period
            """
            return pd.read_sql_query(query, self.connection)

    def _parse_date(self, date_str):
        """Helper method to parse date strings into date objects."""
        if not date_str:
            return None
        try:
            return datetime.datetime.strptime(str(date_str), "%Y-%m-%d").date()
        except ValueError:
            return None