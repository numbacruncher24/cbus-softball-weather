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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Load the page
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            
            # 2. Wait specifically for the iframe (the Google Doc) to appear
            page.wait_for_selector("iframe")
            
            # 3. Target the iframe specifically to ignore the main website's "Trails" headers
            frame = page.frame_locator("iframe")
            
            # Get the text ONLY from inside that frame
            content = frame.locator("body").inner_text()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            browser.close()
            
            results = []
            for park in MY_PARKS:
                for i, line in enumerate(lines):
                    if park.lower() in line.lower():
                        # The status in a Google Doc is usually the very next line
                        if i + 1 < len(lines):
                            status_text = lines[i+1]
                            
                            # Standardized Emoji Logic
                            status_upper = status_text.upper()
                            if "OPEN" in status_upper or "SCHEDULED" in status_upper:
                                emoji = "🟢"
                            elif "CLOSED" in status_upper or "SEASON" in status_upper:
                                emoji = "🔴"
                            else:
                                emoji = "🟡"
                            
                            results.append(f"{emoji} **{park}**: {status_text}")
                        break
            
            return "\n".join(results)
            
        except Exception as e:
            if browser: browser.close()
            return f"⚠️ Scraper Error: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    if not WEBHOOK_URL:
        print("Error: Set DISCORD_WEBHOOK in GitHub Secrets")
        exit()

    park_summary = get_park_data()
    
    # Final Fallback if nothing is found
    if not park_summary:
        park_summary = "⚠️ **Update:** Parks data is currently loading or unavailable."

    current_time = int(time.time())
    content = (
        "🏟️ **LIVE FIELD CONDITIONS**\n"
        f"Last Checked: <t:{current_time}:R>\n\n"
        f"{park_summary}\n\n"
        "🔗 [Official Status Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"
    )

    if MESSAGE_ID:
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"SUCCESS! New Message ID: {r.json()['id']}")
