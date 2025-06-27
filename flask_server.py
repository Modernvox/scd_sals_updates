import sys
import os
import socket
import logging
import traceback
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve
from config import PRICE_MAP, REVERSE_PRICE_MAP, TIER_LIMITS, load_config, get_resource_path
from stripe_service import StripeService
from database import DatabaseManager
from cloud_database import CloudDatabaseManager
import stripe
import sqlite3
import zipfile
import io
import requests

# Force safe async mode
ASYNC_MODE = "threading"

class FlaskServer:
    def __init__(self, port, stripe_service, api_token: str,
                 latest_bin_assignment_callback, secret_key: str,
                 log_info, log_error, user_data_dir=None):
        if user_data_dir is None:
            user_data_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser("~")), 'SwiftSaleApp')
        os.makedirs(user_data_dir, exist_ok=True)
        log_file = os.path.join(user_data_dir, "swiftsale_flask_server.log")

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger(__name__)

        self.log_info = log_info
        self.log_error = log_error
        self.port = port
        self.stripe_service = stripe_service
        self.api_token = api_token
        self.latest_bin_assignment_callback = latest_bin_assignment_callback

        template_dir = get_resource_path("templates")
        static_dir = get_resource_path("static")

        self.app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
        self.app.config['SECRET_KEY'] = secret_key

        self.limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
        self.limiter.init_app(self.app)

        env = os.environ.get('FLASK_ENV', 'development').lower()
        cors_origins = [f"http://localhost:{port}"] if env == 'production' else "*"
        transports = ["polling", "websocket"]
        self.socketio = SocketIO(self.app, cors_allowed_origins=cors_origins, async_mode=ASYNC_MODE, transports=transports)

        self._register_routes()
        self._register_socketio_events()

    def _get_ngrok_path(self) -> str:
        base = get_resource_path("")
        ngrok_local = os.path.join(base, "ngrok.exe")
        if os.path.isfile(ngrok_local):
            if not os.access(ngrok_local, os.X_OK):
                raise PermissionError(f"ngrok.exe at {ngrok_local} is not executable")
            return ngrok_local

        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        zf.extract("ngrok.exe", base)
        return ngrok_local

    def _register_routes(self):
        @self.app.route('/health')
        def health():
            return jsonify(status="ok"), 200

        @self.app.route('/')
        def index():
            return render_template("index.html")

        @self.app.route('/create-checkout-session', methods=['POST'])
        def create_checkout_session():
            data = request.get_json() or {}
            tier = data.get('tier')
            user_email = data.get('user_email')
            if not tier or not user_email:
                return jsonify(error="Missing tier or user_email"), 400
            price_id = PRICE_MAP.get(tier)
            if not price_id:
                return jsonify(error=f"Unknown tier: {tier}"), 400
            try:
                session = self.stripe_service.create_checkout_session(tier, user_email, request.url_root)
                return jsonify(session), 200
            except Exception as e:
                logging.getLogger(__name__).error(f"Stripe session error: {e}", exc_info=True)
                return jsonify(error=str(e)), 500

        @self.app.route('/subscription-status')
        def subscription_status():
            email = request.args.get('email')
            if not email:
                return jsonify(error="Missing email"), 400
            status = self.stripe_service.get_subscription_status(email)
            return jsonify(status=status), 200

        @self.app.route('/stripe-webhook', methods=['POST'])
        def stripe_webhook():
            payload = request.data
            sig_header = request.headers.get('Stripe-Signature')
            status_code, response = self.stripe_service.handle_webhook(payload, sig_header)
            if isinstance(response, dict):
                return jsonify(response), status_code
            elif isinstance(response, str):
                return response, status_code
            else:
                return "", status_code

    def _register_socketio_events(self):
        @self.socketio.on('connect')
        def on_connect():
            self.log_info("Client connected via SocketIO")

    def start(self):
        self.log_info("Starting Flask server")
        ngrok_path = self._get_ngrok_path()
        self.log_info(f"Using ngrok from: {ngrok_path}")
        serve(self.app, host="127.0.0.1", port=self.port, threads=8)

    def shutdown(self):
        self.log_info("Shutting down Flask server")

if __name__ != "__main__":
    try:
        cfg = load_config()
        # Validate environment variables in production
        required_env_vars = ["DATABASE_URL", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "API_TOKEN", "SECRET_KEY"]
        if os.getenv("ENV", "development") != "development":
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            if missing_vars:
                logging.error(f"Missing environment variables: {', '.join(missing_vars)}")
                raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}. Please set them in the environment.")
        
        cfg = load_config()
        env = os.getenv("ENV", "development").lower()
        if env == "production":
            db = CloudDatabaseManager()
        else:
            db = DatabaseManager()

        stripe_service = StripeService(
            stripe_secret_key=cfg.get("STRIPE_SECRET_KEY", ""),
            webhook_secret=cfg.get("STRIPE_WEBHOOK_SECRET", ""),
            db_manager=db,
            api_token=cfg.get("API_TOKEN", "")
        )
        server = FlaskServer(
            port=int(cfg.get("PORT", 5000)),
            stripe_service=stripe_service,
            api_token=cfg.get("API_TOKEN", ""),
            latest_bin_assignment_callback=lambda: None,
            secret_key=cfg.get("SECRET_KEY", os.urandom(24).hex()),  # Generate random secret if missing
            log_info=logging.getLogger(__name__).info,
            log_error=logging.getLogger(__name__).error
        )
        app = server.app
    except Exception as e:
        logging.getLogger(__name__).exception(f"Failed to initialize FlaskServer: {e}")
        raise