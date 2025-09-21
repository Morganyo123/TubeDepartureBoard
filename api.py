from flask import Flask, request, jsonify, send_from_directory
import requests
import controller  # our shared state

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, "control.html")

@app.route('/stations')
def stations():
    q = request.args.get("q")
    if not q:
        return jsonify([])
    resp = requests.get(f"https://api.tfl.gov.uk/StopPoint/Search?query={q}")
    if resp.ok:
        js = resp.json()
        results = [
            {"id": item["id"], "name": item["name"]}
            for item in js.get("matches", [])
            if item["id"].startswith("940G") or item["id"].startswith("HUB")
        ]
        return jsonify(results)

    return jsonify([])

@app.route('/set_station', methods=['POST'])
def set_station():
    data = request.get_json()
    station_id = data.get("id")
    station_name = data.get("name")
    if station_id:
        controller.set_station(station_id, station_name)
        print("Station updated to:", station_name, station_id)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "missing id"}), 400


