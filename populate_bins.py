import sqlite3

DB_PATH = r"C:\Users\lovei\SCD_SALES\swiftsaleapp\bidders.db"

# Paste in only the real, lowercase usernames (omit "new buyer!" and any invalid entries)
user_list = [
    "angieric51333",
    "annakin97567",
    "bjmaz",
    "christinec56706",
    "coltsie",
    "dawnlowe0926",
    "debbiepaq",
    "heathermar1989",
    "jordynnlep",
    "lakydajon",
    "levellen",
    "michaelwhi13289",
    "michelledur1970",
    "millies_closet",
    "modernvarietypopupstore",
    "ortizedi",
    "panther1334",
    "peggyscloset828",
    "sandrasid",
    "shelbystreasures626",
    "tabithalep",
    "tanyalee40315",
    "travelgirl6214",
    "trishboden826",
    "tyronetate",
    "unclaimedfinds",
    "victoriaalm",
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS bin_assignments (
        username TEXT PRIMARY KEY,
        bin_number INTEGER NOT NULL
    );
""")
for u in user_list:
    cursor.execute(
        "INSERT OR REPLACE INTO bin_assignments (username, bin_number) VALUES (?, ?);",
        (u, 1)  # assign bin=1 for every test user
    )
conn.commit()
conn.close()

print(f"Inserted {len(user_list)} usernames into bin_assignments.")
