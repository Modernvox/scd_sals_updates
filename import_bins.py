import sqlite3, csv, os

BASE_DIR = os.path.dirname(__file__)
DB_PATH  = os.path.join(BASE_DIR, "bidders.db")
CSV_PATH = os.path.join(BASE_DIR, "matched_bins.csv")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Clear out any old rows if you like (so you only have exactly the matches)
cur.execute("DELETE FROM bin_assignments;")

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        uname = row["username"].strip().lower()
        bin_num = int(row["bin_number"])
        cur.execute(
            "INSERT OR REPLACE INTO bin_assignments (username, bin_number) VALUES (?, ?)",
            (uname, bin_num)
        )

conn.commit()
conn.close()
print("Imported matched_bins.csv into bin_assignments.")
