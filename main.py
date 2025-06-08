from flask import Flask, jsonify

app = Flask(__name__)

SHOWS = [
    {
        "title": "Snack Crate Blowout!",
        "date": "June 10, 7:00 PM EST",
        "url": "https://www.whatnot.com/live/snackcrate-june10"
    },
    {
        "title": "Mystery Merch Monday",
        "date": "June 12, 5:30 PM EST",
        "url": "https://www.whatnot.com/live/mystery-monday"
    },
    {
        "title": "Brand Name Blowout",
        "date": "June 15, 8:00 PM EST",
        "url": "https://www.whatnot.com/live/brand-blowout"
    }
]

@app.route("/shows")
def get_shows():
    return jsonify(SHOWS)
