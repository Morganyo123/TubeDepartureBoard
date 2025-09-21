import threading

from api import app
from main import run_gui

def run_flask():
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)

if __name__ == "__main__":

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    run_gui()
