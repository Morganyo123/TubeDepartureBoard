from queue import Queue

queue: Queue = None  # set by run.py at startup

# Shared state
station_name: str = "Kings Cross St Pancras"  # default TFL station
bg_color: tuple = (0,0,0)       # GUI background color

# Reference to the API queue for immediate fetch
api_queue_ref: Queue = None

def handle_command(data: dict):
    """
    Push command to GUI queue.
    Updates station_name or bg_color if provided.
    Immediately fetch TFL API on station change.
    """
    global station_name, bg_color

    # Update station name
    if "station_name" in data:
        station_name = data["station_name"]
        # Trigger immediate fetch
        if api_queue_ref is not None:
            try:
                station = controller.station_name
                station_id = get_station_id(station)

                url = f"https://api.tfl.gov.uk/StopPoint/{station_id}/Arrivals"

                import requests
                resp = requests.get(url, timeout=2)
                if resp.ok:
                    api_queue_ref.put(resp.json())
            except Exception:
                pass

    # Update background color
    if "bg_color" in data:
        color = data["bg_color"]
        if isinstance(color, (list, tuple)) and len(color) == 3:
            bg_color = tuple(color)

    if queue is not None:
        queue.put(data)

    return {"status": "queued", "station_name": station_name, "bg_color": bg_color}
