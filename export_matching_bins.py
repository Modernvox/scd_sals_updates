import sqlite3
import pdfplumber
import re
import csv
import os

# ──────────────────────────────────────────────────────────────────────────────
# 1) Adjust these paths:
# ──────────────────────────────────────────────────────────────────────────────
# Point to the PDF in your Downloads folder:
PDF_PATH = r"C:\Users\lovei\Downloads\52704b6d-8e0b-4713-b85c-fea00d7fc6a9.pdf"

# Point to your bidders.db in the swiftsaleapp folder:
DB_PATH  = r"C:\Users\lovei\SCD_SALES\swiftsaleapp\bidders.db"

# Name for the CSV output (it will be written next to this script):
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "matched_bins.csv")
# ──────────────────────────────────────────────────────────────────────────────


def extract_username_from_text(page_text: str) -> str:
    """
    Same logic as annotate_labels.py: Look for "Ships to:", "Pickup to:" or "Pickup Address:",
    then take the first parentheses group on the next non-empty line.
    Returns the username (lowercased, no parentheses), or None if it’s not valid.
    """
    lines = page_text.splitlines()
    for idx, line in enumerate(lines):
        trimmed = line.strip().lower()
        if (
            trimmed.startswith("ships to:") or
            trimmed.startswith("pickup to:") or
            trimmed.startswith("pickup address:")
        ):
            for nxt in lines[idx + 1 :]:
                if not nxt.strip():
                    continue
                m = re.search(r"\(([^)]+)\)", nxt)
                if m:
                    candidate = m.group(1).strip().lower()
                    # Reject anything with spaces or exclamation points (e.g. "new buyer!")
                    if " " in candidate or "!" in candidate:
                        return None
                    return candidate
                return None
            break
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Step 1: Extract all valid usernames from the PDF
# ──────────────────────────────────────────────────────────────────────────────
found_usernames = set()

with pdfplumber.open(PDF_PATH) as pdf:
    for p in pdf.pages:
        text = p.extract_text() or ""
        uname = extract_username_from_text(text)
        if uname:
            found_usernames.add(uname)

if not found_usernames:
    print("No valid '(username)' entries were found in the PDF. Exiting.")
    exit(0)

print("Usernames extracted from PDF:")
for u in sorted(found_usernames):
    print("  •", u)
print()

# ──────────────────────────────────────────────────────────────────────────────
# Step 2: Query bidders.db for those usernames that actually have a bin
# ──────────────────────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Make sure the table exists (it should already, but this won’t hurt):
cur.execute("""
    CREATE TABLE IF NOT EXISTS bin_assignments (
        username   TEXT PRIMARY KEY,
        bin_number INTEGER NOT NULL
    );
""")
conn.commit()

matched = []
for uname in sorted(found_usernames):
    cur.execute("SELECT bin_number FROM bin_assignments WHERE username = ?", (uname,))
    row = cur.fetchone()
    if row:
        matched.append((uname, row[0]))

conn.close()

if not matched:
    print("None of the extracted usernames were found in bin_assignments. Exiting.")
    exit(0)

print("Usernames found in bin_assignments (with their bin_number):")
for u, b in matched:
    print(f"  • {u}: {b}")
print()

# ──────────────────────────────────────────────────────────────────────────────
# Step 3: Write those matches to matched_bins.csv
# ──────────────────────────────────────────────────────────────────────────────
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outcsv:
    writer = csv.writer(outcsv)
    writer.writerow(["username", "bin_number"])
    for u, b in matched:
        writer.writerow([u, b])

print(f"Wrote {len(matched)} rows to '{OUTPUT_CSV}'.")
print("You can now import this CSV back into bin_assignments or inspect it.")
