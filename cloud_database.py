# cloud_database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

class CloudDatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

    def update_subscription(self, user_email, tier, license_key):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO subscriptions (email, tier, license_key)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET tier = EXCLUDED.tier, license_key = EXCLUDED.license_key
            """, (user_email, tier, license_key))
            self.conn.commit()

    def load_subscription_by_id(self, license_key):
        with self.conn.cursor() as cur:
            cur.execute("SELECT email, tier, license_key FROM subscriptions WHERE license_key = %s", (license_key,))
            row = cur.fetchone()
            return (row['email'], row['tier'], row['license_key']) if row else (None, None, None)
