import sqlite3

# Path to your live subscriptions.db
DB_PATH = r"C:\Users\lovei\SCD_SALES\swiftsaleapp\subscriptions.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1) Add current_period_end (expiration timestamp)
try:
    cursor.execute("""
        ALTER TABLE subscriptions
        ADD COLUMN current_period_end INTEGER NOT NULL DEFAULT 0;
    """)
    print("Added column: current_period_end")
except sqlite3.OperationalError:
    # Column already exists
    print("current_period_end already exists, skipping")

# 2) Add is_trial flag (1 = trial, 0 = normal)
try:
    cursor.execute("""
        ALTER TABLE subscriptions
        ADD COLUMN is_trial INTEGER NOT NULL DEFAULT 0;
    """)
    print("Added column: is_trial")
except sqlite3.OperationalError:
    print("is_trial already exists, skipping")

conn.commit()
conn.close()
print("Subscription schema migration complete.")
