import threading
from queue import Queue

from server import controller
from server.api import app
from gui.main import run_gui

def run_flask():
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)

if __name__ == "__main__":
    global APP_ID, APP_KEY
    APP_ID = "Display Project"
    APP_KEY = "fb6d4a48be924109a746cc024894159f"



    command_queue = Queue()
    controller.queue = command_queue

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    run_gui(command_queue)
