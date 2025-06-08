from flask import Flask, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

DATA_FILE = os.path.join(os.getcwd(), "latest_shows.json")

@app.route("/shows")
def get_shows():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return jsonify(data.get("shows", []))
    else:
        return jsonify([])  # Empty if file doesn't exist yet

if __name__ == "__main__":
    app.run(debug=True)
