# controller.py
from threading import Lock

_lock = Lock()
_current_station_id = None
_current_station_name = None

def set_station(station_id, station_name):
    global _current_station_id, _current_station_name
    with _lock:
        _current_station_id = station_id
        _current_station_name = station_name

def get_station():
    with _lock:
        return _current_station_id, _current_station_name
