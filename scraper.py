from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# ─── SETUP HEADLESS BROWSER ───────────────────────────
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

service = Service("C:/Users/lovei/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# ─── NAVIGATE TO PAGE ─────────────────────────────────
print("Loading Whatnot page...")
driver.get("https://www.whatnot.com/user/scdsales")

try:
    # Wait up to 15 seconds for show cards to load
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="show-card"]'))
    )
except Exception as e:
    print("❌ Timeout: Show cards never appeared.")
    driver.quit()
    exit()

# ─── SCRAPE SHOWS ─────────────────────────────────────
cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="show-card"]')
print(f"Found {len(cards)} show cards.")
shows = []

for card in cards:
    try:
        title = card.find_element(By.CSS_SELECTOR, '[data-testid="show-title"]').text.strip()
        date = card.find_element(By.CSS_SELECTOR, '[data-testid="show-time"]').text.strip()
        link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
        shows.append({"title": title, "date": date, "url": link})
    except Exception as e:
        print("⚠️ Error parsing a card:", e)

driver.quit()

# ─── SAVE TO JSON ─────────────────────────────────────
with open("shows.json", "w", encoding="utf-8") as f:
    json.dump(shows, f, indent=2)

print(f"✅ Scraped and saved: {len(shows)} shows.")
