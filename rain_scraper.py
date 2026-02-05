import os
import time
import requests
from playwright.sync_api import sync_playwright

def capture_sheet_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # We use a tall viewport to make sure we get the full sheet
        page = browser.new_page(viewport={'width': 1100, 'height': 1400})
        
        try:
            # Go to the city page
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            
            # Find the iframe and wait for the "Sports" text to load inside it
            page.wait_for_selector("iframe")
            frame = page.frame_locator("iframe").first
            
            # Wait 8 seconds to ensure the spreadsheet finishes loading
            time.sleep(8)
            
            # Take a screenshot of the frame specifically
            frame_handle = page.query_selector("iframe")
            frame_handle.screenshot(path="status_screenshot.png")
            
            browser.close()
            return True
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            if browser: browser.close()
            return False

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    if capture_sheet_screenshot():
        payload = {
            "content": f"🏟️ **LIVE FIELD STATUS SHEET**\nLast Checked: <t:{int(time.time())}:R>"
        }
        
        with open("status_screenshot.png", "rb") as f:
            files = {"file": ("status_screenshot.png", f)}
            
            if MESSAGE_ID:
                # EDIT the existing message
                url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
                r = requests.patch(url, data=payload, files=files)
                print(f"Edit Response: {r.status_code}")
            else:
                # POST a new message (to get the ID initially)
                url = f"{WEBHOOK_URL}?wait=true"
                r = requests.post(url, data=payload, files=files)
                if r.status_code == 200:
                    new_id = r.json()['id']
                    print(f"SUCCESS! New Message ID: {new_id}")
                    print("--- COPY THE ID ABOVE AND ADD IT AS A SECRET NAMED MESSAGE_ID ---")
