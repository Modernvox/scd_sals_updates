import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import socket
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.storage import MemoryStorage
from waitress import serve
from stripe_service import StripeService
from database import DatabaseManager
from config import load_config  # Updated to load_config

# Configure logging with rotation
log_file = os.path.join(os.path.abspath('.'), "flask_dev_debug.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)

# Force safe async mode
ASYNC_MODE = "threading"
logging.info(f"FORCING ASYNC_MODE = {ASYNC_MODE}")

# Load configuration
CONFIG = load_config()
PORT = int(CONFIG.get("PORT", 8000))
SECRET_KEY = CONFIG["SECRET_KEY"]
API_TOKEN = CONFIG["API_TOKEN"]

# Setup StripeService
db = DatabaseManager()
stripe_svc = StripeService(
    stripe_secret_key=CONFIG["STRIPE_SECRET_KEY"],
    webhook_secret=CONFIG["STRIPE_WEBHOOK_SECRET"],
    db_manager=db,
    api_token=API_TOKEN
)

# Handle sys._MEIPASS for frozen apps
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    logging.info(f"🧊 Frozen mode: using BASE_DIR = {BASE_DIR}")
else:
    BASE_DIR = os.path.abspath(".")
    logging.info(f"🛠️ Dev mode: using BASE_DIR = {BASE_DIR}")

TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")

# Verify template directory
if not os.path.exists(TEMPLATE_FOLDER):
    logging.error(f"Template directory not found: {TEMPLATE_FOLDER}")
    sys.exit(1)
if not os.path.exists(os.path.join(TEMPLATE_FOLDER, "index.html")):
    logging.error(f"index.html not found in {TEMPLATE_FOLDER}")
    sys.exit(1)

# Setup Flask app
app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
app.config["SECRET_KEY"] = SECRET_KEY

limiter = Limiter(app=app, key_func=get_remote_address, default_storage=MemoryStorage())
logging.info("Using in-memory storage for rate limiting")

# Setup SocketIO
socketio = SocketIO(app, cors_allowed_origins=f"http://localhost:{PORT}", async_mode=ASYNC_MODE)

# Routes
@app.route('/health')
def health():
    logging.info("Health check accessed")
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    logging.info(f"TEMPLATE DIR: {app.template_folder}")
    logging.info(f"index.html exists: {os.path.exists(os.path.join(app.template_folder, 'index.html'))}")
    return render_template("index.html")

@app.route('/get_latest')
def get_latest():
    return jsonify({"data": "Waiting for bidder..."})

@app.route('/create-checkout-session', methods=["POST"])
@limiter.limit("10 per minute")
def create_checkout_session():
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    tier = data.get("tier")
    email = data.get("user_email")
    if not tier or not email:
        return jsonify({"error": "Missing tier or user_email"}), 400

    result, status = stripe_svc.create_checkout_session(tier, email, request.url_root)
    return jsonify(result), status

@app.route('/stripe-webhook', methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature')
    status, resp = stripe_svc.handle_webhook(payload, sig)
    return jsonify(resp or {'status': 'success'}), status

@app.route('/shutdown', methods=["GET"])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
        logging.info("Server shut down")
        return "Server shut down", 200
    return "Shutdown not supported", 200

# SocketIO events
@socketio.on("connect")
def handle_connect():
    logging.info("Client connected to SocketIO")
    socketio.emit("update", {"data": "Waiting for bidder..."})

# Launch server
def start_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", PORT))
    except OSError as e:
        logging.error(f"Port {PORT} is already in use: {e}")
        sys.exit(1)

    env_mode = os.environ.get("FLASK_ENV", "development").lower()
    if env_mode == "production":
        logging.info(f"🏭 Waitress serving on 0.0.0.0:{PORT}")
        serve(app, host="0.0.0.0", port=PORT, threads=8)
    else:
        logging.info(f"🧪 Dev server on 127.0.0.1:{PORT}")
        socketio.run(app, host="127.0.0.1", port=PORT, debug=True, use_reloader=False)

if __name__ == "__main__":
    start_server()