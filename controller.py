
from threading import Lock

_lock = Lock()
_current_station_id = "940GZZLUKSX"
_current_station_name = "Kings Cross and St Pancras"

def set_station(station_id, station_name):
    global _current_station_id, _current_station_name
    with _lock:
        _current_station_id = station_id
        _current_station_name = station_name

def get_station():
    with _lock:
        return _current_station_id, _current_station_name
