# build_hub_to_tube_children.py
import requests
import json

def get_tube_children(hub_id):
    """Return only Tube child StopPoint IDs (those starting with 940G) for a hub."""
    resp = requests.get(f"https://api.tfl.gov.uk/StopPoint/{hub_id}", timeout=5)
    if not resp.ok:
        return []
    js = resp.json()
    children = js.get("children", [])
    # filter to only tube stop points (id starting with 940G)
    return [c["id"] for c in children if c["id"].startswith("940G")]

# 1. Get all StopPoints for tube mode
resp = requests.get("https://api.tfl.gov.uk/StopPoint/mode/tube", timeout=10)
resp.raise_for_status()
stop_points = resp.json().get("stopPoints", [])

# 2. Collect all hub IDs (those starting with HUB)
hub_ids = [sp["id"] for sp in stop_points if sp["id"].startswith("HUB")]

hub_to_children = {}
for hub in hub_ids:
    print("Fetching children for", hub)
    tube_children = get_tube_children(hub)
    if tube_children:
        hub_to_children[hub] = tube_children

# 3. Save the dict to JSON
with open("hub_to_tube_children.json", "w") as f:
    json.dump(hub_to_children, f, indent=2)

print("Saved hub_to_tube_children.json with", len(hub_to_children), "entries.")
