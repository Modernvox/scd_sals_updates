import pdfplumber
import re

def extract_username_from_text(page_text: str) -> str:
    """
    Same logic as in annotate_labels.py: look for a marker line like "Ships to:" or
    "Pickup to:" or "Pickup Address:", then grab the first (...) on the very next non-empty line.
    Returns the username without parentheses, lowercased; otherwise None.
    """
    lines = page_text.splitlines()
    for idx, line in enumerate(lines):
        trimmed = line.strip().lower()
        if trimmed.startswith("ships to:") or trimmed.startswith("pickup to:") or trimmed.startswith("pickup address:"):
            for nxt in lines[idx + 1 :]:
                if not nxt.strip():
                    continue
                m = re.search(r"\(([^)]+)\)", nxt)
                if m:
                    return m.group(1).strip().lower()
                else:
                    return None
            break
    return None

PDF_PATH = r"C:\Users\lovei\Downloads\52704b6d-8e0b-4713-b85c-fea00d7fc6a9.pdf"

usernames = set()

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        u = extract_username_from_text(text)
        if u:
            usernames.add(u)

print("Found these usernames (one per page, according to extract logic):")
for u in sorted(usernames):
    print("  •", u)
