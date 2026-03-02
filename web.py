from flask import Flask
from config import PORT
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Rename Bot Running"

def run():
    app.run(host="0.0.0.0", port=PORT)

def start():
    t = threading.Thread(target=run)
    t.start()
