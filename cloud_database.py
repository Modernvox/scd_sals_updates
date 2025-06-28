import os
import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError

class CloudDatabaseManager:
    def __init__(self):
        self._connect()

    def _connect(self):
        try:
            self.conn = psycopg2.connect(
                os.getenv("DATABASE_URL"),
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        except OperationalError as e:
            raise RuntimeError("Could not connect to PostgreSQL") from e

    def _ensure_connection(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1;")
            cur.close()
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self._connect()  # Reconnect

    def update_subscription(self, user_email, tier, license_key):
        self._ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO subscriptions (email, tier, license_key)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    tier = EXCLUDED.tier,
                    license_key = EXCLUDED.license_key
            """, (user_email, tier, license_key))
            self.conn.commit()

    def load_subscription_by_id(self, license_key):
        self._ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute("SELECT email, tier, license_key FROM subscriptions WHERE license_key = %s", (license_key,))
            row = cur.fetchone()
            return (row['email'], row['tier'], row['license_key']) if row else (None, None, None)
