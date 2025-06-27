import pdfplumber
import re
import csv
import os

# ──────────────────────────────────────────────────────────────────────────────
# 1) Paths – adjust the PDF path if needed
# ──────────────────────────────────────────────────────────────────────────────
PDF_PATH = r"C:\Users\lovei\Downloads\52704b6d-8e0b-4713-b85c-fea00d7fc6a9.pdf"

# We will write the CSV next to this script:
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "assigned_bins.csv")
# ──────────────────────────────────────────────────────────────────────────────


def extract_username_from_text(page_text: str) -> str:
    """
    Same as in annotate_labels.py:
    Look for a line starting with "Ships to:", "Pickup to:", or "Pickup Address:",
    then grab the first parentheses group on the very next non-blank line.
    Returns the username (lowercased, no parentheses), or None if not found/invalid.
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
                    # Skip anything that isn't a “no spaces, no punctuation” username
                    if " " in candidate or "!" in candidate:
                        return None
                    return candidate
                return None
            break
    return None


def main():
    # 2) Open the PDF and extract usernames in page order
    assigned = []  # list of (username, bin_number)
    seen = set()   # avoid duplicate usernames if that ever happens

    with pdfplumber.open(PDF_PATH) as pdf:
        bin_number = 1
        for page_index, pg in enumerate(pdf.pages):
            text = pg.extract_text() or ""
            uname = extract_username_from_text(text)
            if uname and uname not in seen:
                assigned.append((uname, bin_number))
                seen.add(uname)
                bin_number += 1

    if not assigned:
        print("No valid usernames found in the PDF. Exiting.")
        return

    # 3) Write assigned_bins.csv
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "bin_number"])
        for uname, bn in assigned:
            writer.writerow([uname, bn])

    print(f"Wrote {len(assigned)} rows to '{OUTPUT_CSV}':")
    for uname, bn in assigned:
        print(f"  • {uname}: {bn}")


if __name__ == "__main__":
    main()
