import sqlite3
import time

# Path to your live subscriptions.db
DB_PATH = r"C:\Users\lovei\SCD_SALES\swiftsaleapp\subscriptions.db"

def grant_one_month_silver_trial(db_path: str, user_email: str, days: int = 30):
    """
    Upserts a row in subscriptions so that:
      - email = user_email
      - tier = 'Silver'
      - license_key = NULL     (you can adjust or leave as-is)
      - current_period_end = now + days*24*60*60
      - is_trial = 1
    If the user already exists, it overwrites those fields.
    """
    now_ts = int(time.time())
    expire_ts = now_ts + days * 24 * 60 * 60  # 30 days from now

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure table exists (just in case; it does already from step 1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            email               TEXT PRIMARY KEY,
            tier                TEXT NOT NULL,
            license_key         TEXT,
            current_period_end  INTEGER NOT NULL,
            is_trial            INTEGER NOT NULL
        );
    """)

    # Upsert logic (SQLite 3.24+ ON CONFLICT syntax)
    cursor.execute("""
        INSERT INTO subscriptions (email, tier, license_key, current_period_end, is_trial)
        VALUES (:email, 'Silver', NULL, :expire_ts, 1)
        ON CONFLICT(email) DO UPDATE SET
            tier = 'Silver',
            license_key = NULL,
            current_period_end = :expire_ts,
            is_trial = 1
    """, {
        "email": user_email,
        "expire_ts": expire_ts
    })

    conn.commit()
    conn.close()
    print(f"Granted Silver trial to {user_email} until {time.ctime(expire_ts)}")

if __name__ == "__main__":
    # Change this to the actual email you want to grant
    grant_one_month_silver_trial(DB_PATH, "alice@example.com", days=30)
