import os
import time
import requests
from playwright.sync_api import sync_playwright

def capture_sheet_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # We use a tall viewport to capture the whole list
        page = browser.new_page(viewport={'width': 1000, 'height': 1200})
        
        try:
            # 1. Load the page
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            
            # 2. Find the iframe and wait for it to be visible
            page.wait_for_selector("iframe")
            frame_handle = page.query_selector("iframe")
            
            # 3. Take a screenshot of just that iframe element
            # We add a 5s sleep to ensure the spreadsheet data actually 'pops in'
            time.sleep(5)
            frame_handle.screenshot(path="status_screenshot.png")
            
            browser.close()
            return True
        except Exception as e:
            print(f"Error: {e}")
            if browser: browser.close()
            return False

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    
    if capture_sheet_screenshot():
        # Prepare the Discord Message
        payload = {
            "content": f"🏟️ **LATEST FIELD STATUS SHEET**\nLast Checked: <t:{int(time.time())}:R>"
        }
        
        # Upload the actual image file to Discord
        with open("status_screenshot.png", "rb") as f:
            files = {"file": ("status_screenshot.png", f)}
            r = requests.post(WEBHOOK_URL, data=payload, files=files)
            
        if r.status_code == 200:
            print("Screenshot posted successfully!")
    else:
        # Fallback if screenshot fails
        requests.post(WEBHOOK_URL, json={"content": "⚠️ **Update:** Failed to capture the status sheet. [Check Manually](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"})
