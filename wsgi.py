from flask_server import FlaskServer
from stripe_service import StripeService
from config import load_config
from database import DatabaseManager
import logging

cfg = load_config()
db = DatabaseManager()
stripe_service = StripeService(
    stripe_secret_key=cfg["STRIPE_SECRET_KEY"],
    webhook_secret=cfg["STRIPE_WEBHOOK_SECRET"],
    db_manager=db,
    api_token=cfg["API_TOKEN"]
)

server = FlaskServer(
    port=int(cfg.get("PORT", 5000)),
    stripe_service=stripe_service,
    api_token=cfg["API_TOKEN"],
    latest_bin_assignment_callback=lambda: "N/A",
    secret_key=cfg["SECRET_KEY"],
    log_info=logging.getLogger(__name__).info,
    log_error=logging.getLogger(__name__).error
)

app = server.app  # This is what Gunicorn will use
