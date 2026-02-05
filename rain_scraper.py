import os
import time
import requests
import json
from playwright.sync_api import sync_playwright

def capture_sheet_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1100, 'height': 1400})
        try:
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            page.wait_for_selector("iframe")
            frame_handle = page.query_selector("iframe")
            time.sleep(8)
            frame_handle.screenshot(path="status_screenshot.png")
            browser.close()
            return True
        except Exception as e:
            print(f"Error: {e}")
            if browser: browser.close()
            return False

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    if capture_sheet_screenshot():
        # This payload tells Discord to:
        # 1. Update the text content
        # 2. Clear out all OLD attachments (the 'attachments': [] part)
        payload_json = {
            "content": f"🏟️ **LIVE FIELD STATUS SHEET**\nLast Checked: <t:{int(time.time())}:R>",
            "attachments": [] 
        }
        
        with open("status_screenshot.png", "rb") as f:
            # We must use 'payload_json' as a string when sending files via PATCH
            files = {
                "file": ("status_screenshot.png", f),
                "payload_json": (None, json.dumps(payload_json))
            }
            
            if MESSAGE_ID:
                url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
                # PATCH now includes instructions to wipe the old image
                r = requests.patch(url, files=files)
                print(f"Overwrite Status: {r.status_code}")
            else:
                url = f"{WEBHOOK_URL}?wait=true"
                r = requests.post(url, data={"payload_json": json.dumps(payload_json)}, files={"file": ("status_screenshot.png", f)})
                if r.status_code == 200:
                    print(f"SUCCESS! New Message ID: {r.json()['id']}")
