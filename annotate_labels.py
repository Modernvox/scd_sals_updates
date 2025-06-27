import sqlite3
import pdfplumber
import re
import io

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --------------------------------------------------------------------------
# Configuration: 4"×6" page (in points: 72 pt = 1")
# --------------------------------------------------------------------------
LABEL_WIDTH = 4 * inch    # 288 pts
LABEL_HEIGHT = 6 * inch   # 432 pts
PAGE_SIZE = (LABEL_WIDTH, LABEL_HEIGHT)


def extract_username_from_text(page_text: str) -> str:
    """
    Given the text of a single 4"x6" Whatnot page, find the buyer's username
    (always inside parentheses) immediately after one of these markers:
       • "Ships to:"
       • "Pickup to:"
       • "Pickup Address:"
    Ignores "(NEW BUYER!)" and returns the next username (lowercased, without parentheses) if found; otherwise None.
    """
    lines = page_text.splitlines()
    for idx, line in enumerate(lines):
        trimmed = line.strip().lower()
        if (
            trimmed.startswith("ships to:") or
            trimmed.startswith("pickup to:") or
            trimmed.startswith("pickup address:")
        ):
            # Look at subsequent non-empty lines for any "(username)" after "(NEW BUYER!)"
            for nxt in lines[idx + 1:]:
                if not nxt.strip():
                    continue
                # Search for any username in parentheses
                m = re.search(r"\(([^)]+)\)", nxt)
                if m:
                    username = m.group(1).strip().lower()
                    # Skip if it's "(NEW BUYER!)", otherwise return the username
                    if username != "new buyer!":
                        return username
            break
    return None


def annotate_whatnot_pdf_with_bins_skip_missing(
    whatnot_pdf_path: str,
    bidders_db_path: str,
    output_pdf_path: str,
    stamp_x: float = 2.8 * inch,  # Default x offset set to 2.8 inches
    stamp_y: float = 5.2 * inch,  # Default y offset set to 5.2 inches
    font_name: str = "Helvetica-Bold",
    font_size_app: int = 10,
    font_size_bin: int = 14,
    font_size_default: int = 10  # New smaller font size for "Possible" and "(Givvy/FlashSale)"
) -> list:
    """
    Annotate a Whatnot-exported 4"x6" PDF (one label/slip per page) by stamping:
        SwiftSale App:
        Bin [number]    (if username matches)
        Possible        (if no username match)
        (Givvy/FlashSale)    (if no username match, on next line)
    at the specified position (default: 2.8" x, 5.2" y) for every instance a username appears.

    Returns a list of (page_index, username) for pages that had a "(username)"
    but where no bin was found in the DB. All other pages are either stamped or copied unchanged.
    """

    # 1) Build a lookup dict: lowercase username → bin_number
    conn = sqlite3.connect(bidders_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username, bin_number FROM bin_assignments;")
    rows = cursor.fetchall()
    conn.close()

    bin_map = {row[0].strip().lower(): row[1] for row in rows}

    # 2) Open the Whatnot PDF (for stamping with PyPDF2 & text extraction with pdfplumber)
    pdf_reader = PdfReader(whatnot_pdf_path)
    pdf_writer = PdfWriter()
    skipped_pages = []

    # Open pdfplumber just once
    with pdfplumber.open(whatnot_pdf_path) as plumber_pdf:
        for page_index in range(len(pdf_reader.pages)):
            original_page = pdf_reader.pages[page_index]
            plumber_page = plumber_pdf.pages[page_index]
            page_text = plumber_page.extract_text() or ""

            # 3a) Find the "(username)" in the text
            username = extract_username_from_text(page_text)
            if not username:
                # No "(username)" → copy page as-is
                pdf_writer.add_page(original_page)
                continue

            # 3b) Look up bin_number
            bin_number = bin_map.get(username)
            if bin_number is None:
                # Found "(username)" but no bin in DB → stamp "Possible" and "(Givvy/FlashSale)" and record
                skipped_pages.append((page_index, username))
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=PAGE_SIZE)

                # Draw "SwiftSale App:" 4 pts above the "Possible" line
                can.setFont(font_name, font_size_app)
                can.drawString(stamp_x, stamp_y + font_size_default + 4, "SwiftSale App:")

                # Draw "Possible" at (stamp_x, stamp_y)
                can.setFont(font_name, font_size_default)
                can.drawString(stamp_x, stamp_y, "Possible")

                # Draw "(Givvy/FlashSale)" on the next line, 8 pts below "Possible"
                can.drawString(stamp_x, stamp_y - font_size_default, "(Givvy/FlashSale)")

                can.save()
                packet.seek(0)

                overlay_pdf = PdfReader(packet)
                overlay_page = overlay_pdf.pages[0]
                original_page.merge_page(overlay_page)
                pdf_writer.add_page(original_page)
                continue

            # 4) Create an in-memory overlay that stamps at the specified position for matched usernames
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=PAGE_SIZE)

            # Draw "SwiftSale App:" 4 pts above the bin line
            can.setFont(font_name, font_size_app)
            can.drawString(stamp_x, stamp_y + font_size_bin + 4, "SwiftSale App:")

            # Draw "Bin [number]" at (stamp_x, stamp_y)
            can.setFont(font_name, font_size_bin)
            can.drawString(stamp_x, stamp_y, f"Bin {bin_number}")

            can.save()
            packet.seek(0)

            # 5) Merge overlay onto the original page
            overlay_pdf = PdfReader(packet)
            overlay_page = overlay_pdf.pages[0]
            original_page.merge_page(overlay_page)
            pdf_writer.add_page(original_page)

    # 6) Write out the annotated PDF
    with open(output_pdf_path, "wb") as out_f:
        pdf_writer.write(out_f)

    return skipped_pages