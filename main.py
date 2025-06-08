from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

DATA_FILE = os.path.join(os.getcwd(), "latest_shows.json")

@app.route("/shows", methods=["GET", "POST"])
def shows():
    if request.method == "POST":
        data = request.get_json()
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return jsonify({"status": "success"}), 200

    elif request.method == "GET":
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return jsonify(data.get("shows", []))
        return jsonify([])

if __name__ == "__main__":
    app.run(debug=True)
