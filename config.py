import os
import sys
import logging

# ─── ENVIRONMENT CHECK ─────────────────────────────────────────────
IS_PROD = os.environ.get("RENDER", "") == "true"

# ─── STATIC MAPS & CONSTANTS ───────────────────────────────────────
PRICE_MAP = {
    "Bronze": "price_1RLcP4J7WrcpTNl6a8aHdSgv",
    "Silver": "price_1RLcKcJ7WrcpTNl6jT7sLvmU",
    "Gold":   "price_1RQefvJ7WrcpTNl68QwN2zEj",
}
REVERSE_PRICE_MAP = {v: k for k, v in PRICE_MAP.items()}

DEFAULT_DATA_DIR = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser("~")), "SwiftSaleApp")
PRIMARY_COLOR = "#378474"

# ─── EMAIL PERSISTENCE ("Remember Me") ────────────────────────────────
import json

REMEMBER_ME_PATH = os.path.join(DEFAULT_DATA_DIR, "remember_me.json")

def save_email(email: str):
    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    with open(REMEMBER_ME_PATH, "w") as f:
        json.dump({"email": email}, f)

def load_email() -> str:
    try:
        with open(REMEMBER_ME_PATH, "r") as f:
            return json.load(f).get("email", "")
    except Exception:
        return ""

def clear_saved_email():
    try:
        os.remove(REMEMBER_ME_PATH)
    except FileNotFoundError:
        pass

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

# ─── HARDCODED CONFIG (Dev/Offline Only) ────────────────────────────

def load_config() -> dict:
    if IS_PROD:
        # Load from Render environment
        return {
            'STRIPE_PUBLIC_KEY':     os.environ["STRIPE_PUBLIC_KEY"],
            'STRIPE_SECRET_KEY':     os.environ["STRIPE_SECRET_KEY"],
            'STRIPE_WEBHOOK_SECRET': os.environ["STRIPE_WEBHOOK_SECRET"],
            'API_TOKEN':             os.environ["API_TOKEN"],
            'SECRET_KEY':            os.environ["SECRET_KEY"],
            'NGROK_AUTH_TOKEN':      os.environ.get("NGROK_AUTH_TOKEN", ""),
            'DEV_OVERRIDE_SECRET':   os.environ.get("DEV_OVERRIDE_SECRET", ""),
            'USER_EMAIL':            os.environ.get("USER_EMAIL", ""),
            'PORT':                  os.environ.get("PORT", "8000"),
            'APP_BASE_URL':          os.environ.get("APP_BASE_URL", f"http://localhost:{os.environ.get('PORT', '8000')}"),
            'DATABASE_URL':          "sqlite:///subscriptions.db"
        }
    else:
        ensure_data_dir()
        db_file = os.path.join(DEFAULT_DATA_DIR, "subscriptions.db")

        return {
            'STRIPE_PUBLIC_KEY':     "gAAAAABoOhNCjxM8ftO-NNGMzKXH9YKdEjgvuw60IYuIjQLMSzn92Ox2PE3QeG45hzXds7Ojb1s2G_X1bnd3H_6DI0Op4hNcbl6fZ-WaVSJ3UB58kSFtFrl_Ezdx8fqQtnYtOmzD4pofdCFCpMMWr89CleLTrasDr3Y3QdhmEb_SAtdl9shTPdDIFa8ylCwFlI_-hdkaBiidukdF2iE66LU-gAML9INrGQ==",
            'STRIPE_SECRET_KEY':     "gAAAAABoOhNCjh26r-e2Tx8Yt8wRYxQnhTZgGR96HSLE3II8r6PYiR1L0thKc1gBB7pXUF4dKy18lRbPanhS3DEnKeGCuITAI3UunnmTzGc3tUv3Tgs1c3eFU1PWp5Lwwqiuuc_W1W2ln0CG1ahJJ6PAXB6Wq7AZvm2zTxZoSMEgLhyvk08FPx2brdCrD4jJBgusb9BMme8Dqiad73lVGQau_n-fhocAgg==",
            'STRIPE_WEBHOOK_SECRET': "gAAAAABoOhNCbgXHPZQxYeHLz4_8CXrn64_IWqUjNaXS1bHWjFQ_ZOeRAae2dfZdextwyqZdq7G3bPCcoOXYJ6HPYEXHDwGgIxDPL0GZewGZe1p8jFFMkOdZJDHY1nNqsg3I35M3t9rL",
            'API_TOKEN':             "gAAAAABoOhNCg3LOv7ddQZ16Ye-1B_Pn-EtIWnQ7FhgP31BfNsclRfvARWazBrOLeu-mnPTaFDAV6U2-vBEQZxvk_hTGvd8lF-nDnKnk_-v6HU5oCfTt5TzjnX_jhxf6wixvWFH_cMAs",
            'SECRET_KEY':            "gAAAAABoOhNCnSEfaC4ucB0svrt7BSZVQWtlLONsfArLdwIfWM7irQmb4VhKXWODnmEiiqePuh8AUWlwuNgsc7lpx1YzfG0MqENsRIASY3aMoVfG3B1_Sr8oCpS2k5YAlj1wis5yuzPx",
            'NGROK_AUTH_TOKEN':      "gAAAAABoOhNCvpN3_445IiaB4JKGqHCpoiYY9yXh0PUGyQ8mH3bXf78agyOAsGr6SRVqkmKOxn_yCWS0tBcHyL3UWNwqIGiNklMDGjK9pnjZ4_my-A3KQ516q0YpgM0mhXBkBwkDaE5hv9sWwXN2_CZOuMsLo_hcIQ==",
            'DEV_OVERRIDE_SECRET':   "gAAAAABoOhNCEVTg8f2pQoA63W_TK8ZhWvDiD0yLGZxOFWHMQoeD8NgfRKCqgjj3wycbBl5KbXuNv4d58iHmdbpPv-skJ1IJfA==",
            'USER_EMAIL':            os.getenv("USER_EMAIL", ""),
            'PORT':                  os.getenv("PORT", "8000"),
            'APP_BASE_URL':          os.getenv("APP_BASE_URL", f"http://localhost:{os.getenv('PORT', '8000')}"),
            'DATABASE_URL':          f"sqlite:///{db_file}"
        }

# ─── EXPORT ENVIRONMENT VARIABLES ───────────────────────────────────────
config = load_config()

STRIPE_PUBLIC_KEY     = config['STRIPE_PUBLIC_KEY']
STRIPE_SECRET_KEY     = config['STRIPE_SECRET_KEY']
STRIPE_WEBHOOK_SECRET = config['STRIPE_WEBHOOK_SECRET']
API_TOKEN             = config['API_TOKEN']
SECRET_KEY            = config['SECRET_KEY']
NGROK_AUTH_TOKEN      = config['NGROK_AUTH_TOKEN']
DEV_OVERRIDE_SECRET   = config['DEV_OVERRIDE_SECRET']
USER_EMAIL            = config['USER_EMAIL']
PORT                  = config['PORT']
APP_BASE_URL          = config['APP_BASE_URL']
DATABASE_URL          = config['DATABASE_URL']
