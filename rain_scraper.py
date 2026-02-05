import os
import time
import requests
from playwright.sync_api import sync_playwright

def capture_sheet_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1000, 'height': 1200})
        try:
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            page.wait_for_selector("iframe")
            frame_handle = page.query_selector("iframe")
            time.sleep(7) # Increased wait to ensure grid lines load
            frame_handle.screenshot(path="status_screenshot.png")
            browser.close()
            return True
        except Exception as e:
            print(f"Error: {e}")
            if browser: browser.close()
            return False

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID') # Required for overwriting
    
    if capture_sheet_screenshot():
        payload = {
            "content": f"🏟️ **LIVE FIELD STATUS SHEET**\nLast Checked: <t:{int(time.time())}:R>"
        }
        
        with open("status_screenshot.png", "rb") as f:
            files = {"file": ("status_screenshot.png", f)}
            
            if MESSAGE_ID:
                # OVERWRITE existing message
                # Note: We use PATCH to edit the message with the new file
                url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
                r = requests.patch(url, data=payload, files=files)
            else:
                # INITIAL POST (Run this once to get your ID)
                url = f"{WEBHOOK_URL}?wait=true"
                r = requests.post(url, data=payload, files=files)
                if r.status_code == 200:
                    print(f"SUCCESS! New Message ID: {r.json()['id']}")
                    print("ADD THIS ID TO GITHUB SECRETS AS 'MESSAGE_ID'")
