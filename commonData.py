import queue
from collections import deque
import pandas as pd
from datetime import datetime
import numpy as np

class DataHouse:
    def __init__(self):
        self._init_data_structures()
        self.queue = queue.Queue(maxsize=1000)

    def _init_data_structures(self):
        self.data = {
            'timestamp': deque(maxlen=1000),
            'speed': deque(maxlen=1000),
            'objects': deque(maxlen=1000),
            'area': deque(maxlen=1000)
        }

    def add_data(self, speed, objects, area):
        self.data['timestamp'].append(datetime.now())
        self.data['speed'].append(int(speed))
        self.data['objects'].append(int(objects))
        self.data['area'].append(int(area))

    def get_dataframe(self):
        return pd.DataFrame(self.data)

