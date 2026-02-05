import os
import time
import requests
from playwright.sync_api import sync_playwright

# The 4 parks from your image
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

def get_park_data():
    # Start Playwright
    with sync_playwright() as p:
        # Launch browser (headless = no window)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Go to the main page
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            
            # 2. WAIT for the Google Doc iframe to load its content
            # We wait for the text "Sports" to appear inside the frame
            page.wait_for_timeout(5000) # 5-second buffer for slow loads
            
            # 3. Get all text from the page (including inside the iframe)
            # Playwright handles the 'frame' barrier automatically here
            content = page.locator("body").inner_text()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            browser.close()
            
            results = []
            for park in MY_PARKS:
                for i, line in enumerate(lines):
                    if park.lower() in line.lower():
                        # The status is usually the next line
                        if i + 1 < len(lines):
                            status_text = lines[i+1]
                            
                            # Emoji Logic
                            if any(word in status_text.upper() for word in ["OPEN", "SCHEDULED"]):
                                emoji = "🟢"
                            elif any(word in status_text.upper() for word in ["CLOSED", "SEASON"]):
                                emoji = "🔴"
                            else:
                                emoji = "🟡"
                            
                            results.append(f"{emoji} **{park}**: {status_text}")
                        break
            
            return "\n".join(results)
            
        except Exception as e:
            browser.close()
            return f"⚠️ Scraper Error: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    if not WEBHOOK_URL:
        print("Missing DISCORD_WEBHOOK secret.")
        exit()

    park_summary = get_park_data()
    
    if not park_summary:
        park_summary = "⚠️ **Update:** No park data found. The website might be undergoing maintenance."

    # Final Discord Message
    content = (
        "🏟️ **LIVE FIELD CONDITIONS**\n"
        f"Last Checked: <t:{int(time.time())}:R>\n\n"
        f"{park_summary}\n\n"
        "🔗 [Official Status Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"
    )

    # Webhook Logic
    if MESSAGE_ID:
        # Update existing message
        url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
        requests.patch(url, json={"content": content})
    else:
        # Post new message and print ID
        url = f"{WEBHOOK_URL}?wait=true"
        r = requests.post(url, json={"content": content})
        if r.status_code == 200:
            print(f"SUCCESS! New Message ID: {r.json()['id']}")
            print("Copy this ID into your GitHub Secrets as MESSAGE_ID")
