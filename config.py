import os
import sys
import logging

# ─── Try to import get_machine_key if local ────────────────────────────────
try:
    from encrypt_keys import get_machine_key
except ImportError:
    get_machine_key = None
    logging.warning("encrypt_keys.py not found — assuming production environment.")

# ─── LOAD .env (optional, but not required) ─────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.debug("python-dotenv not installed; skipping .env load")

# ─── STATIC MAPS & CONSTANTS ────────────────────────────────────────────────

PRICE_MAP = {
    "Bronze": "price_1RLcP4J7WrcpTNl6a8aHdSgv",
    "Silver": "price_1RLcKcJ7WrcpTNl6jT7sLvmU",
    "Gold":   "price_1RQefvJ7WrcpTNl68QwN2zEj",
}
REVERSE_PRICE_MAP = {v: k for k, v in PRICE_MAP.items()}

DEFAULT_DATA_DIR = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser("~")), "SwiftSaleApp")

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
    if not get_machine_key:
        raise ConfigError("Local decryption unavailable — missing encrypt_keys.py")

    fernet = get_machine_key()

    encrypted_keys = {
        'STRIPE_PUBLIC_KEY':      'gAAAAABoOhNCjxM8ftO-NNGMzKXH9YKdEjgvuw60IYuIjQLMSzn92Ox2PE3QeG45hzXds7Ojb1s2G_X1bnd3H_6DI0Op4hNcbl6fZ-WaVSJ3UB58kSFtFrl_Ezdx8fqQtnYtOmzD4pofdCFCpMMWr89CleLTrasDr3Y3QdhmEb_SAtdl9shTPdDIFa8ylCwFlI_-hdkaBiidukdF2iE66LU-gAML9INrGQ==',
        'STRIPE_SECRET_KEY':      'gAAAAABoOhNCjh26r-e2Tx8Yt8wRYxQnhTZgGR96HSLE3II8r6PYiR1L0thKc1gBB7pXUF4dKy18lRbPanhS3DEnKeGCuITAI3UunnmTzGc3tUv3Tgs1c3eFU1PWp5Lwwqiuuc_W1W2ln0CG1ahJJ6PAXB6Wq7AZvm2zTxZoSMEgLhyvk08FPx2brdCrD4jJBgusb9BMme8Dqiad73lVGQau_n-fhocAgg==',
        'STRIPE_WEBHOOK_SECRET':  'gAAAAABoOhNCbgXHPZQxYeHLz4_8CXrn64_IWqUjNaXS1bHWjFQ_ZOeRAae2dfZdextwyqZdq7G3bPCcoOXYJ6HPYEXHDwGgIxDPL0GZewGZe1p8jFFMkOdZJDHY1nNqsg3I35M3t9rL',
        'API_TOKEN':              'gAAAAABoOhNCg3LOv7ddQZ16Ye-1B_Pn-EtIWnQ7FhgP31BfNsclRfvARWazBrOLeu-mnPTaFDAV6U2-vBEQZxvk_hTGvd8lF-nDnKnk_-v6HU5oCfTt5TzjnX_jhxf6wixvWFH_cMAs',
        'SECRET_KEY':             'gAAAAABoOhNCnSEfaC4ucB0svrt7BSZVQWtlLONsfArLdwIfWM7irQmb4VhKXWODnmEiiqePuh8AUWlwuNgsc7lpx1YzfG0MqENsRIASY3aMoVfG3B1_Sr8oCpS2k5YAlj1wis5yuzPx',
        'DEV_OVERRIDE_SECRET':    'gAAAAABoOhNCEVTg8f2pQoA63W_TK8ZhWvDiD0yLGZxOFWHMQoeD8NgfRKCqgjj3wycbBl5KbXuNv4d58iHmdbpPv-skJ1IJfA==',
        'NGROK_AUTH_TOKEN':       'gAAAAABoOhNCvpN3_445IiaB4JKGqHCpoiYY9yXh0PUGyQ8mH3bXf78agyOAsGr6SRVqkmKOxn_yCWS0tBcHyL3UWNwqIGiNklMDGjK9pnjZ4_my-A3KQ516q0YpgM0mhXBkBwkDaE5hv9sWwXN2_CZOuMsLo_hcIQ=='
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

# ─── LOAD ENVIRONMENT CONFIG ────────────────────────────────────────────────

if os.environ.get("RENDER", "0") == "1":
    STRIPE_PUBLIC_KEY     = os.environ["STRIPE_PUBLIC_KEY"]
    STRIPE_SECRET_KEY     = os.environ["STRIPE_SECRET_KEY"]
    STRIPE_WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]
    API_TOKEN             = os.environ["API_TOKEN"]
    SECRET_KEY            = os.environ["SECRET_KEY"]
    NGROK_AUTH_TOKEN      = os.environ.get("NGROK_AUTH_TOKEN", "")
    DEV_OVERRIDE_SECRET   = os.environ.get("DEV_OVERRIDE_SECRET", "")

    USER_EMAIL            = os.environ.get("USER_EMAIL", "")
    PORT                  = os.environ.get("PORT", "8000")
    APP_BASE_URL          = os.environ.get("APP_BASE_URL", f"http://localhost:{PORT}")
    DATABASE_URL          = "sqlite:///subscriptions.db"
else:
    _keys = load_encrypted_keys()

    STRIPE_PUBLIC_KEY     = _keys['STRIPE_PUBLIC_KEY']
    STRIPE_SECRET_KEY     = _keys['STRIPE_SECRET_KEY']
    STRIPE_WEBHOOK_SECRET = _keys['STRIPE_WEBHOOK_SECRET']
    API_TOKEN             = _keys['API_TOKEN']
    SECRET_KEY            = _keys['SECRET_KEY']
    NGROK_AUTH_TOKEN      = _keys['NGROK_AUTH_TOKEN']
    DEV_OVERRIDE_SECRET   = _keys['DEV_OVERRIDE_SECRET']

    USER_EMAIL            = _keys['USER_EMAIL']
    PORT                  = _keys['PORT']
    APP_BASE_URL          = _keys['APP_BASE_URL']
    DATABASE_URL          = _keys['DATABASE_URL']

# ─── EXPORT LOAD FUNCTION FOR MODULES THAT CALL load_config() ───────────────
load_config = load_encrypted_keys

if __name__ == "__main__":
    print("PORT:", PORT)
    print("APP_BASE_URL:", APP_BASE_URL)
    print("DATABASE_URL:", DATABASE_URL)
    if not os.environ.get("RENDER"):
        cfg["ENV"] = "production"
        
