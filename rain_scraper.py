import os
import time
import requests
from playwright.sync_api import sync_playwright

def get_full_sheet_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        try:
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            page.wait_for_selector("iframe")
            frame = page.frame_locator("iframe").first
            
            # Wait for the data to load
            frame.get_by_text("Sports").wait_for(state="visible", timeout=20000)
            
            # Grab EVERYTHING inside the sheet
            full_content = frame.locator("body").inner_text()
            browser.close()
            return full_content
        except Exception as e:
            if browser: browser.close()
            return f"⚠️ Error loading sheet: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    all_text = get_full_sheet_text()

    # Discord has a 2000 character limit per message
    # We trim it just in case the sheet is massive
    content = (
        "🏟️ **FULL FIELD STATUS SHEET**\n"
        f"Last Checked: <t:{int(time.time())}:R>\n"
        "```\n"
        f"{all_text[:1500]}" 
        "\n```"
    )

    if MESSAGE_ID:
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"New Message ID: {r.json()['id']}")
