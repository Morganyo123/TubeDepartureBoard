import threading
import requests
import time
from queue import Queue, Empty
import json
from pathlib import Path
from flask.cli import prepare_import

import controller


def get_station_id(station_name):
    url = f"https://api.tfl.gov.uk/StopPoint/Search/{station_name}"
    response = requests.get(url)
    data = response.json()
    # Look for individual platforms first
    for match in data.get('matches', []):

        if 'HUB' not in match['id']:
            return match['id']

        else:
            hub_id = match["id"]

            hub_url = f"https://api.tfl.gov.uk/StopPoint/{hub_id}"
            hub_response = requests.get(hub_url)
            hub_data = hub_response.json()

            # Find the first tube platform
            for child in hub_data.get('children', []):
                if any(mode in child['modes'] for mode in ['tube', 'dlr']):
                    return child['id']

    return None

def fake_start_api_fetcher(api_queue: Queue, stop_event, interval=5):
    """
    Fake fetcher – pushes dummy data into the queue every `interval` seconds.
    """
    def loop():
        while not stop_event.is_set():
            fake_data = [
                {"lineName": "Jubilee", "destinationName": "Stratford", "timeToStation": 120,"direction":"Northbound"},
                {"lineName": "Jubilee", "destinationName": "Stanmore", "timeToStation": 300,"direction":"Northbound"},
                {"lineName": "Jubilee", "destinationName": "Stratford", "timeToStation": 480,"direction":"Northbound"},
                {"lineName": "Jubilee", "destinationName": "Stratford", "timeToStation": 480, "direction": "Northbound"},
                {"lineName": "Jubilee", "destinationName": "Stratford", "timeToStation": 480, "direction": "Northbound"},
                {"lineName": "Northern", "destinationName": "Morden", "timeToStation": 90,"direction":"Northbound"},
                {"lineName": "Northern", "destinationName": "High Barnet", "timeToStation": 240,"direction":"Northbound"},
                {"lineName": "Northern", "destinationName": "Edgware", "timeToStation": 420,"direction":"Northbound"},
                {"lineName": "Northern", "destinationName": "Edgware", "timeToStation": 420, "direction": "Northbound"},
                {"lineName": "Northern", "destinationName": "Edgware", "timeToStation": 420, "direction": "Northbound"}
            ]
            api_queue.put(fake_data)
            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t
import pygame

def draw_text_box(screen, text, pos, font, text_color=(255,255,255),
                  box_color=(0,120,200), border_radius=10, padding=(10,5), border_color=None, border_width=2):
    """
    Draw text inside a rounded rectangle on the Pygame screen.

    Args:
        screen: Pygame surface to draw on
        text: string to display
        pos: (x, y) top-left position of the box
        font: Pygame font object
        text_color: color of the text
        box_color: background color of the rounded box
        border_radius: radius of the corners
        padding: (x_padding, y_padding) around text inside box
        border_color: if set, draws a border around the box
        border_width: width of the border (ignored if border_color is None)
    """
    # Render text
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect()

    # Calculate box rect
    box_rect = pygame.Rect(pos[0]-(text_rect.width + 2*padding[0])/2, pos[1]-(text_rect.height + 2*padding[1])/2,
                           text_rect.width + 2*padding[0],
                           text_rect.height + 2*padding[1])

    # Draw border first if specified
    if border_color:
        pygame.draw.rect(screen, border_color, box_rect, border_radius=border_radius)
        # shrink box for inner fill
        inner_rect = box_rect.inflate(-border_width*2, -border_width*2)
        pygame.draw.rect(screen, box_color, inner_rect, border_radius=border_radius)
    else:
        pygame.draw.rect(screen, box_color, box_rect, border_radius=border_radius)

    # Draw text
    text_rect.topleft = (pos[0]-(text_rect.width + 2*padding[0])/2 + padding[0], pos[1]-(text_rect.height + 2*padding[1])/2 + padding[1])
    screen.blit(text_surface, text_rect.topleft)

def start_api_fetcher(api_queue: Queue, stop_event, interval=5):
    """
    Background thread fetching TFL data every interval seconds.
    """
    HUB_TO_CHILDREN = {}
    json_path = Path("hub_to_tube_children.json")
    if json_path.exists():
        with open(json_path) as f:
            HUB_TO_CHILDREN = json.load(f)

    def loop():
        while not stop_event.is_set():
            try:
                station_id , station_name = controller.get_station()

                if station_id.startswith("HUB"):
                    hub_id = station_id

                    hub_url = f"https://api.tfl.gov.uk/StopPoint/{hub_id}"
                    hub_response = requests.get(hub_url)
                    hub_data = hub_response.json()

                    # Find the first tube platform
                    for child in hub_data.get('children', []):
                        if any(mode in child['modes'] for mode in ['tube']):
                            station_id = child['id']



                resp = requests.get(f"https://api.tfl.gov.uk/StopPoint/{station_id}/Arrivals", timeout=5)
                data = resp.json()
                api_queue.put(data)

            except Exception as e:
                print("Error fetching arrivals:", e)

            time.sleep(interval)
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t


def start_weather_fetcher(weather_queue, stop_event, interval=600):
    """
    Fetch current temperature in London every `interval` seconds.
    Using Open-Meteo API (no key needed).
    """
    # London coordinates
    lat, lon = 51.5074, -0.1278

    def loop():
        while not stop_event.is_set():
            try:
                # Example Open-Meteo call:
                url = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={lat}&longitude={lon}"
                    f"&current_weather=true"
                    f"&timezone=Europe/London"
                )
                resp = requests.get(url, timeout=5)
                if resp.ok:
                    js = resp.json()
                    # Open-Meteo returns something like:
                    # { "latitude": ..., "longitude": ..., "current_weather": { "temperature": ..., "windspeed": ..., ... } }
                    temp = js.get("current_weather", {}).get("temperature")
                    if temp is not None:
                        weather_queue.put(temp)
                # else: maybe log
            except Exception as e:
                print("Weather fetch error:", e)
            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t


def run_gui():
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    YELLOW = (255, 191, 0)

    TUBE_LINE_COLORS = {
        "Bakerloo": (178, 99, 0),
        "Central": (220, 36, 31),
        "Circle": (255, 200, 10),
        "District": (0, 125, 50),
        "Hammersmith & City": (245, 137, 166),
        "Jubilee": (131, 141, 147),
        "Metropolitan": (155, 0, 88),
        "Northern": (0, 0, 0),
        "Piccadilly": (0, 25, 168),
        "Victoria": (3, 155, 229),
        "Waterloo & City": (118, 208, 189)}


    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH,HEIGHT = screen.get_size()

    clock = pygame.time.Clock()

    row_font = pygame.font.Font('gui/simple_s.ttf', 36)
    clock_font = pygame.font.Font('gui/simple_s.ttf', 46)

    font_small = pygame.font.Font('gui/simple_s.ttf', 26)
    font_large = pygame.font.Font('gui/simple_s.ttf', 42)


    api_data = None

    current_index = 0
    last_switch = time.time()

    api_queue = Queue()
    stop_event = threading.Event()
    api_thread = start_api_fetcher(api_queue, stop_event, interval=5)

    weather_queue = Queue()
    stop_weather = threading.Event()
    weather_thread = start_weather_fetcher(weather_queue, stop_weather, interval=300)  # e.g. every 5 minutes

    current_temp = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update background color from controller
        bg_color = BLACK

        station_id, station_name = controller.get_station()
        try:
            new_temp = weather_queue.get_nowait()
            current_temp = new_temp
        except Empty:
            pass

        # Handle API data
        try:
            api_data = api_queue.get_nowait()
        except Empty:
            pass

        # Draw GUI
        screen.fill(bg_color)

        #weather
        weather_surface = font_small.render(f'{current_temp:.0f} C', True, YELLOW)
        screen.blit(weather_surface, (10, 10))

        # Date top-right: day and then day+month on separate lines
        day_str = time.strftime("%a")  # e.g. Mon
        date_str = time.strftime("%d %b")  # e.g. 11 Sep

        day_surface = font_small.render(day_str, True, YELLOW)
        date_surface = font_small.render(date_str, True, YELLOW)

        # Align both to top-right
        day_rect = day_surface.get_rect(topright=(WIDTH - 10, 10))
        date_rect = date_surface.get_rect(topright=(WIDTH - 10, 40))  # second line a bit lower

        screen.blit(day_surface, day_rect)
        screen.blit(date_surface, date_rect)

        #header station
        station_surface = font_large.render(f"{station_name}", True, YELLOW)
        station_rect = station_surface.get_rect(midbottom=(WIDTH / 2,40))
        screen.blit(station_surface, station_rect)

        if api_data:
            try:
                from collections import defaultdict
                arrivals_by_line = defaultdict(list)
                for item in api_data:
                    arrivals_by_line[item['lineName']].append(item)
                for line, items in arrivals_by_line.items():
                    items.sort(key=lambda x: x['timeToStation'])

                line_names = list(arrivals_by_line.keys())

                if line_names:  # only if there are lines
                    if time.time() - last_switch > 5:
                        current_index = (current_index + 1) % len(line_names)
                        last_switch = time.time()
                    # clamp current_index just in case
                    if current_index >= len(line_names):
                        current_index = 0
                else:
                    current_index = 0

                current_line = line_names[current_index]

                arrivals = arrivals_by_line[current_line][:4]
                # draw line badge
                draw_text_box(screen, current_line.replace("&","and"), (WIDTH/2, 80), row_font,
                              text_color=WHITE,
                              box_color=TUBE_LINE_COLORS.get(current_line),

                              border_radius=12,
                              padding=(15, 8),
                              border_color=WHITE,
                              border_width=2)

                y = 125
                for i, item in enumerate(arrivals):

                    #destination = item['destinationName']
                    time_sec = item['timeToStation']
                    #direction = item['direction']
                    platform = item['platformName']

                    platform = platform.replace('-', '')
                    minutes = time_sec // 60
                    seconds = time_sec % 60

                    # left side: time + destination
                    dep_surface = row_font.render(f"{i+1}. {platform} ", True, YELLOW)
                    screen.blit(dep_surface, (10, y))

                    # right side: time to departure (aligned to right margin)
                    mins_surface = row_font.render(f"{minutes}min", True, YELLOW)
                    mins_rect = mins_surface.get_rect(topright=(WIDTH - 10, y))
                    screen.blit(mins_surface, mins_rect)


                    y += 80
            except:
                pass
        # Large Clock
        now = time.strftime("%H.%M.%S")
        clock_surface = clock_font.render(now, True, YELLOW)
        clock_rect = clock_surface.get_rect(midbottom=(WIDTH / 2, HEIGHT - 12))
        screen.blit(clock_surface, clock_rect)

        pygame.display.flip()
        clock.tick(30)

    stop_event.set()
    api_thread.join(timeout=1.0)
    weather_thread.join(timeout=1.0)

    pygame.quit()
