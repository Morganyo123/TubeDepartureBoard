import pygame
from datetime import datetime
import sys
import requests


APP_ID = "Display Project"
APP_KEY = "fb6d4a48be924109a746cc024894159f"


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


def get_tube_departures(station_id, max_results=5):
    """
    Simple function to get tube departures
    station_id: Use TfL station code (e.g., '940GZZLUKSX' for King's Cross)
    """
    url = f"https://api.tfl.gov.uk/StopPoint/{station_id}/Arrivals"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        departures = response.json()

        # Sort by time to station
        sorted_departures = sorted(departures, key=lambda x: x['timeToStation'])

        return sorted_departures[:max_results]

    except Exception as e:
        print(f"Error: {e}")




pygame.init()

# === Setup window ===
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # full screen
width, height = screen.get_size()
pygame.display.set_caption("Train Board")

# === Colors & fonts ===
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

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


title_font = pygame.font.Font('gui/LondonTube-MABx.ttf', 32)
row_font = pygame.font.Font('gui/LondonTube-MABx.ttf', 16)

# === Station ====
station = "kings cross"
station_id = get_station_id(station)

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # press ESC to exit
                pygame.quit()
                sys.exit()

    departures = get_tube_departures(station_id)


    # === Draw background ===
    screen.fill(WHITE)

    # === Header ===
    now = datetime.now().strftime("%H:%M")
    header = title_font.render(f"Departures from {station}. ({now})", True, BLACK)
    screen.blit(header, (20, 20))

    # === Draw each departure row ===
    y = 120
    for i, departure in enumerate(departures, 1):
        line = departure['lineName']
        destination = departure['destinationName']
        time_sec = departure['timeToStation']
        minutes = time_sec // 60
        seconds = time_sec % 60

        text = row_font.render(
            f"{i}. {line} to {destination} - {minutes}min", True, TUBE_LINE_COLORS.get(line)
        )
        screen.blit(text, (40, y))

        y += 50

    pygame.display.flip()
    clock.tick(1/10) # 1 fram update every 30secs