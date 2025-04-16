import threading
import queue
from collections import deque
import pandas as pd
from datetime import datetime
import numpy as np
class DataStore:
    def __init__(self):
        self._init_data_structures()
        self.queue = queue.Queue(maxsize=100)
        self.lock = threading.Lock()
        self.update_event = threading.Event()  # New: Event flag for updates

    def _init_data_structures(self):
        self.data = {
            'timestamp': deque(maxlen=1000),
            'speed': deque(maxlen=1000),
            'objects': deque(maxlen=1000),
            'area': deque(maxlen=1000)
        }

    def add_data(self, speed, objects, area):
        with self.lock:
            self.data['timestamp'].append(datetime.now())
            self.data['speed'].append(int(speed))
            self.data['objects'].append(int(objects))
            self.data['area'].append(int(area))
            self.update_event.set()  # Signal new data

    def get_dataframe(self):
        with self.lock:
            self.update_event.clear()  # Reset the flag
            return pd.DataFrame(self.data)

data_store = DataStore()