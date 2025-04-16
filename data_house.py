import queue
from collections import deque
import pandas as pd
from datetime import datetime
import threading

# Global variables
_data = {
    'timestamp': deque(maxlen=1000),
    'speed': deque(maxlen=1000),
    'objects': deque(maxlen=1000),
    'area': deque(maxlen=1000)
}
_queue = queue.Queue(maxsize=1000)
_lock = threading.Lock()

def add_data(speed, objects, area):
    """Thread-safe data addition"""
    print("Adding data")
    _data['timestamp'].append(datetime.now())
    _data['speed'].append(int(speed))
    _data['objects'].append(int(objects))
    _data['area'].append(int(area))

def get_dataframe():
    """Thread-safe DataFrame retrieval"""
    print("Getting data from queue")
    return pd.DataFrame(_data)

def put_to_queue(item):
    """Add item to the global queue"""
    try:
        _queue.put(item, timeout=1.0)
        return True
    except queue.Full:
        return False

def get_from_queue():
    """Get item from the global queue"""
    try:
        return _queue.get_nowait()
    except queue.Empty:
        return None

def get_queue_size():
    """Get current queue size"""
    return _queue.qsize()