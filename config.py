import os
import sys
import logging
from pathlib import Path

# Optional .env loading
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.debug("python-dotenv not installed; skipping .env load")

# Constants & Static Maps
PRICE_MAP = {
    "Bronze": "price_1RLcP4J7WrcpTNl6a8aHdSgv",
    "Silver": "price_1RLcKcJ7WrcpTNl6jT7sLvmU",
    "Gold":   "price_1RQefvJ7WrcpTNl68QwN2zEj",
}
REVERSE_PRICE_MAP = {v: k for k, v in PRICE_MAP.items()}

DEFAULT_DATA_DIR = Path(os.getenv('LOCALAPPDATA', os.path.expanduser("~"))) / "SwiftSaleApp"
PRIMARY_COLOR = "#378474"

TIER_LIMITS = {
    "Trial":   {"bins": 20},
    "Bronze":  {"bins": 50},
    "Silver":  {"bins": 150},
    "Gold":    {"bins": 300},
}

PAYMENT_LINKS = {
    "Bronze": "https://buy.stripe.com/aFa14o2gqcdpenj9LQgw001",
    "Silver": "https://buy.stripe.com/14AdRa5sCa5h92ZcY2gw002",
    "Gold":   "https://buy.stripe.com/28E28s3ku2CPdjfe26gw000",
}

def get_resource_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def ensure_data_dir() -> str:
    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    return DEFAULT_DATA_DIR

class ConfigError(Exception):
    pass

def load_encrypted_keys() -> dict:
    env = os.getenv("ENV", "development")
    if env != "development":
        raise ConfigError("load_encrypted_keys() should only be called in development!")

    try:
        from encrypt_keys import decrypt_keys, get_machine_key
    except ImportError:
        raise RuntimeError("encrypt_keys.py missing — cannot run in local dev without it.")

    fernet = get_machine_key()
    encrypted_keys = {
        'STRIPE_PUBLIC_KEY': '...',
        'STRIPE_SECRET_KEY': '...',
        'STRIPE_WEBHOOK_SECRET': '...',
        'API_TOKEN': '...',
        'SECRET_KEY': '...',
        'NGROK_AUTH_TOKEN': '...',
        'DEV_OVERRIDE_SECRET': '...',
    }

    decrypted = {}
    for k, blob in encrypted_keys.items():
        try:
            decrypted[k] = fernet.decrypt(blob.encode()).decode()
        except Exception as e:
            logging.error(f"Failed to decrypt {k}: {e}")
            raise ConfigError(f"Failed to decrypt {k}")

    decrypted['USER_EMAIL'] = os.getenv("USER_EMAIL", "")
    decrypted['PORT'] = os.getenv("PORT", "8000")
    decrypted['APP_BASE_URL'] = os.getenv("APP_BASE_URL", f"http://localhost:{decrypted['PORT']}")
    ensure_data_dir()
    db_file = os.path.join(DEFAULT_DATA_DIR, "subscriptions.db")
    decrypted['DATABASE_URL'] = f"sqlite:///{db_file}"

    return decrypted

def load_config():
    env = os.getenv("ENV", "production")  # default to production
    config = {
        "API_TOKEN": os.getenv("API_TOKEN", ""),
        "USER_EMAIL": os.getenv("USER_EMAIL", ""),
        "APP_BASE_URL": os.getenv("APP_BASE_URL", "http://localhost:5000"),
        "PORT": int(os.getenv("PORT", "5000")),
        "DEV_UNLOCK_CODE": os.getenv("DEV_UNLOCK_CODE", ""),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
        "DATABASE_URL": os.getenv("DATABASE_URL", "")  # add this to prevent crash
    }

    # Load decrypt_keys only in dev mode
    if env == "development":
        try:
            from encrypt_keys import load_encrypted_keys
            config.update(load_encrypted_keys())
        except (ImportError, Exception) as e:
            print(f"[config.py] Skipping encrypted keys in dev: {e}")
            pass

    return config

if __name__ == "__main__":
    cfg = load_config()
    print("PORT:", cfg.get("PORT"))
    print("APP_BASE_URL:", cfg.get("APP_BASE_URL"))
    print("DATABASE_URL:", cfg.get("DATABASE_URL"))