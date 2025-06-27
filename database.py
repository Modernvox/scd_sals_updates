# database.py
import os
import sqlite3
import logging
import shutil
from config import load_config, DEFAULT_DATA_DIR

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            user_data_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser("~")), 'SwiftSaleApp')
            os.makedirs(user_data_dir, exist_ok=True)
            db_path = os.path.join(user_data_dir, 'subscriptions.db')

        config = load_config()
        database_url = config.get("DATABASE_URL", f"sqlite:///{db_path}")
        if not database_url and os.getenv("ENV", "development") == "production":
            logging.error("DATABASE_URL is required in production")
            raise ValueError("DATABASE_URL is required in production")

        if not database_url.startswith("sqlite:///"):
            logging.error(f"Only SQLite is supported: {database_url}")
            raise ValueError("Only SQLite is supported")

        if not os.path.exists(db_path):
            install_dir = os.path.dirname(os.path.abspath(__file__))
            src_db = os.path.join(install_dir, 'subscriptions.db')
            if os.path.exists(src_db):
                shutil.copy(src_db, db_path)
                logging.info(f"Copied database from {src_db} to {db_path}")
            else:
                logging.info(f"Source database not found at {src_db}, creating new database")

        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.db_path = db_path
            logging.info(f"Connected to SQLite database: {db_path}")
            self._initialize_database()
            self._migrate_database()
        except sqlite3.Error as e:
            logging.error(f"Database connection failed for {db_path}: {e}")
            raise

    def _initialize_database(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                email TEXT PRIMARY KEY,
                tier TEXT NOT NULL,
                license_key TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                email TEXT PRIMARY KEY,
                chat_id TEXT,
                top_buyer_text TEXT,
                giveaway_announcement_text TEXT,
                flash_sale_announcement_text TEXT,
                multi_buyer_mode BOOLEAN
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bin_assignments (
                username TEXT PRIMARY KEY,
                bin_number INTEGER NOT NULL
            )
        """)
        self.conn.commit()
        logging.info("Database tables initialized successfully")

    def _migrate_database(self):
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(settings)")
        columns = [col[1] for col in cursor.fetchall()]
        if "multi_buyer_mode" not in columns:
            logging.info("Migrating settings table to add multi_buyer_mode column")
            cursor.execute("""
                CREATE TABLE settings_new (
                    email TEXT PRIMARY KEY,
                    chat_id TEXT,
                    top_buyer_text TEXT,
                    giveaway_announcement_text TEXT,
                    flash_sale_announcement_text TEXT,
                    multi_buyer_mode BOOLEAN
                )
            """)
            cursor.execute("""
                INSERT INTO settings_new (email, chat_id, top_buyer_text, giveaway_announcement_text, flash_sale_announcement_text)
                SELECT email, chat_id, top_buyer_text, giveaway_announcement_text, flash_sale_announcement_text
                FROM settings
            """)
            cursor.execute("DROP TABLE settings")
            cursor.execute("ALTER TABLE settings_new RENAME TO settings")
            self.conn.commit()
            logging.info("Migration completed: added multi_buyer_mode column")

    def save_subscription(self, email, tier, license_key):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO subscriptions (email, tier, license_key) VALUES (?, ?, ?)",
            (email, tier, license_key)
        )
        self.conn.commit()
        logging.info(f"Saved subscription for {email}: tier={tier}, license_key={license_key}")

    def get_subscription(self, email):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT email, tier, license_key FROM subscriptions WHERE email = ?", (email,)
        )
        result = cursor.fetchone()
        if result:
            return {"email": result[0], "tier": result[1], "license_key": result[2]}
        return None

    def get_settings(self, email):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT email, chat_id, top_buyer_text, giveaway_announcement_text, flash_sale_announcement_text, multi_buyer_mode FROM settings WHERE email = ?",
            (email,)
        )
        result = cursor.fetchone()
        if result:
            return {
                "email": result[0],
                "chat_id": result[1],
                "top_buyer_text": result[2],
                "giveaway_announcement_text": result[3],
                "flash_sale_announcement_text": result[4],
                "multi_buyer_mode": bool(result[5])
            }
        return None

    def save_settings(self, email, chat_id, top_buyer_text, giveaway_announcement_text, flash_sale_announcement_text, multi_buyer_mode):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (
                email, chat_id, top_buyer_text, giveaway_announcement_text, flash_sale_announcement_text, multi_buyer_mode
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (email, chat_id, top_buyer_text, giveaway_announcement_text, flash_sale_announcement_text, int(multi_buyer_mode)))
        self.conn.commit()
        logging.info(f"Saved settings for {email}")

    def update_subscription(self, email, tier, license_key):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT email FROM subscriptions WHERE email = ?", (email,)
        )
        if cursor.fetchone():
            cursor.execute(
                "UPDATE subscriptions SET tier = ?, license_key = ? WHERE email = ?", (tier, license_key, email)
            )
        else:
            cursor.execute(
                "INSERT INTO subscriptions (email, tier, license_key) VALUES (?, ?, ?)",
                (email, tier, license_key)
            )
        self.conn.commit()
        logging.info(f"Updated subscription for {email}: tier={tier}, license_key={license_key}")

    def load_subscription(self, email):
        sub = self.get_subscription(email)
        return (sub["email"], sub["tier"], sub["license_key"]) if sub else (None, None, None)

    def load_subscription_by_license_key(self, license_key):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT email, tier, license_key FROM subscriptions WHERE license_key = ?", (license_key,)
        )
        result = cursor.fetchone()
        return (result[0], result[1], result[2]) if result else (None, None, None)

    def count_user_bins(self, user_email: str) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM bin_assignments WHERE username = ?",
                (user_email,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            logging.error(f"Failed to count bins for {user_email}: {e}", exc_info=True)
            return 0

    def close(self):
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")
