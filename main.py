
import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
import tkinter as tk
from tkinter import messagebox
import requests
import socket
import threading
import redis

from gui_dev import SwiftSaleGUI
from config import load_config
from database import DatabaseManager
from stripe_service import StripeService
from flask_server import FlaskServer

# ─── USER DATA & LOG SETUP ────────────────────────────────────────────────

user_data_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser("~")), 'SwiftSaleApp')
os.makedirs(user_data_dir, exist_ok=True)

os.environ["FLASK_ENV"] = "production"

log_file = os.path.join(user_data_dir, "swiftsale_app.log")

def custom_log(level, message):
    """Write timestamped message to both console (if available) and log file."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"{timestamp} [{level}] {message}\n"

    # Attempt console output if stdout is available
    try:
        if getattr(sys, 'stdout', None):
            sys.stdout.write(log_message)
    except Exception:
        pass

    # Always append to our log file
    try:
        with open(log_file, 'a') as f:
            f.write(log_message)
    except Exception as e:
        try:
            sys.stderr.write(f"Failed to write to log file: {e}\n")
        except Exception:
            pass

def log_info(message):
    logging.info(message)
    custom_log("INFO", message)

def log_error(message, exc_info=False):
    logging.error(message, exc_info=exc_info)
    custom_log("ERROR", message)

# Configure root logger
try:
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    stream = sys.stdout if getattr(sys, 'stdout', None) else sys.stderr
    stream_handler = logging.StreamHandler(stream)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])
    log_info(f"Logging configured to write to {log_file}")
except Exception as e:
    try:
        sys.stderr.write(f"Failed to configure logging: {e}\n")
    except Exception:
        pass

def log_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    else:
        log_error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception

# ─── UTILITIES ────────────────────────────────────────────────────────────

def wait_for_server(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                log_info("Flask server health check passed")
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise RuntimeError("Flask server did not start in time")

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False

def find_open_port(start_port=8000, max_attempts=10):
    port = start_port
    for _ in range(max_attempts):
        if check_port(port):
            return port
        port += 1
    raise RuntimeError(f"No available ports between {start_port} and {start_port + max_attempts - 1}")

def check_redis(url):
    try:
        r = redis.Redis.from_url(url)
        r.ping()
        log_info("Redis connection successful")
        return True
    except redis.ConnectionError as e:
        log_error(f"Redis connection failed: {e}")
        return False

# ─── MAIN ─────────────────────────────────────────────────────────────────

def main():
    log_info("Starting SwiftSale GUI")

    try:
        config = load_config()
    except Exception as e:
        log_error(f"Failed to load configuration: {e}", exc_info=True)
        messagebox.showerror("Configuration Error", str(e))
        sys.exit(1)

    # Redact secrets for logging
    redacted = {}
    for k, v in config.items():
        if "KEY" in k or "TOKEN" in k or "secret" in k.lower():
            redacted[k] = "<REDACTED>"
        else:
            redacted[k] = v
    log_info(f"Loaded config: {redacted}")
    print(f"Loaded config: {redacted}")

    # Dynamic port and base URL
    port = find_open_port(int(config.get("PORT", 8000)))
    config["PORT"] = str(port)
    config["APP_BASE_URL"] = f"http://localhost:{port}"
    log_info(f"Using dynamic port: {port}")

    # Validate required keys
    required = [
        "STRIPE_SECRET_KEY", "STRIPE_PUBLIC_KEY", "STRIPE_WEBHOOK_SECRET",
        "API_TOKEN", "PORT", "SECRET_KEY", "APP_BASE_URL"
    ]
    missing = [k for k in required if not config.get(k)]
    if missing:
        log_error(f"Configuration is missing: {missing}")
        messagebox.showerror("Configuration Error",
                             f"Missing configuration key(s): {', '.join(missing)}")
        sys.exit(1)

    # Initialize components
    db = DatabaseManager(db_path=os.path.join(user_data_dir, 'subscriptions.db'))
    stripe = StripeService(
        stripe_secret_key=config["STRIPE_SECRET_KEY"],
        webhook_secret=config["STRIPE_WEBHOOK_SECRET"],
        db_manager=db,
        api_token=config["API_TOKEN"]
    )

    flask_server = FlaskServer(
        port=port,
        stripe_service=stripe,
        api_token=config["API_TOKEN"],
        latest_bin_assignment_callback=lambda: "Waiting for bidder…",
        secret_key=config["SECRET_KEY"],
        log_info=log_info,
        log_error=log_error,
        user_data_dir=user_data_dir
    )
    server_thread = threading.Thread(target=flask_server.start, daemon=True)
    server_thread.start()

    wait_for_server(f"http://localhost:{port}/health")

    # Launch GUI
    root = tk.Tk()
    root.withdraw()
    log_info(f"Passing base_url to SwiftSaleGUI: {config['APP_BASE_URL']}")
    app = SwiftSaleGUI(
        master=root,
        stripe_service=stripe,
        api_token=config["API_TOKEN"],
        user_email=config["USER_EMAIL"],
        base_url=config["APP_BASE_URL"],
        dev_unlock_code=config.get("DEV_OVERRIDE_SECRET", ""),
        telegram_bot_token=config.get("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=config.get("TELEGRAM_CHAT_ID", ""),
        log_info=log_info,
        log_error=log_error
    )
    root.deiconify()

    def on_closing():
        try:
            db.close()
            flask_server.shutdown()
        except Exception as e:
            log_error(f"Error during shutdown: {e}")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
