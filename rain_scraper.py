import os
import time
import requests
from playwright.sync_api import sync_playwright

# Shortened names for better matching
MY_PARKS = ["Anheuser-Busch", "Cooper", "Berliner", "Spindler"]

def get_park_data():
    with sync_playwright() as p:
        # 1. Launch a real browser (headless)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 2. Go to the main City Website
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            
            # 3. Wait for the iframe to exist on the page
            page.wait_for_selector("iframe", timeout=15000)
            
            # 4. Target the Google Sheet iframe specifically
            # This 'flattens' the iframe so we can see the text inside
            frame = page.frame_locator("iframe").first
            
            # 5. Get all the text content inside that specific frame
            content = frame.locator("body").inner_text()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            browser.close()
            
            results = []
            for park in MY_PARKS:
                for i, line in enumerate(lines):
                    if park.lower() in line.lower():
                        # Scrape the status from the lines immediately following the park name
                        for offset in range(1, 4):
                            if i + offset < len(lines):
                                status_candidate = lines[i + offset]
                                status_upper = status_candidate.upper()
                                if any(word in status_upper for word in ["OPEN", "CLOSED", "SCHEDULED", "SEASON"]):
                                    emoji = "🟢" if "OPEN" in status_upper or "SCHEDULED" in status_upper else "🔴"
                                    results.append(f"{emoji} **{park}**: {status_candidate}")
                                    break
                        break
            
            return "\n".join(results)
            
        except Exception as e:
            if browser: browser.close()
            return f"⚠️ Iframe Error: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    park_summary = get_park_data()
    
    if not park_summary:
        park_summary = "⚠️ **Update:** Connected to website, but couldn't see the data inside the window."

    content = (
        "🏟️ **LIVE FIELD CONDITIONS**\n"
        f"Last Checked: <t:{int(time.time())}:R>\n\n"
        f"{park_summary}\n\n"
        "🔗 [Official Status Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"
    )

    if MESSAGE_ID:
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"SUCCESS! New Message ID: {r.json()['id']}")
