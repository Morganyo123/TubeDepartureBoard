from flask import Flask, request, jsonify, send_from_directory
from . import controller

app = Flask(__name__, static_folder="static")

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json(force=True)
    return controller.handle_command(data)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "control.html")
