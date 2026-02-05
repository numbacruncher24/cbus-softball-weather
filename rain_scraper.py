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
        # Launch the browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Go to the main page
            page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
            
            # 2. Focus on the iframe where the Google Doc lives
            # This ignores the "Trails" and "Athletics" headers on the main site
            frame_element = page.frame_locator("iframe")
            
            # 3. Wait for the Google Doc content to load inside that frame
            # We wait for a park name to be visible inside the iframe
            frame_element.get_by_text("Berliner").wait_for(timeout=10000)
            
            # 4. Extract the text from ONLY the Google Doc
            content = frame_element.locator("body").inner_text()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            browser.close()
            
            results = []
            for park in MY_PARKS:
                for i, line in enumerate(lines):
                    if park.lower() in line.lower():
                        # The status is usually the next line in the Google Doc
                        if i + 1 < len(lines):
                            status_text = lines[i+1]
                            
                            # Emoji Logic
                            status_upper = status_text.upper()
                            if any(word in status_upper for word in ["OPEN", "SCHEDULED"]):
                                emoji = "🟢"
                            elif any(word in status_upper for word in ["CLOSED", "SEASON"]):
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
        print("Error: DISCORD_WEBHOOK secret is missing.")
        exit()

    park_summary = get_park_data()
    
    # Final Fallback
    if not park_summary:
        park_summary = "⚠️ **Update:** No park data found. The website might be loading slowly."

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
