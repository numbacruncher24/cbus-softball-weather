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

# This is the direct 'Publish to Web' link for the Google Doc
DOC_URL = "https://docs.google.com/document/d/e/2PACX-1vT5K8nL7Bf1_fR_YJ-Xo-U0o5X8nL7Bf1_fR_YJ-Xo-U0o5X8/pub?embedded=true"

def get_park_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Go directly to the Google Doc source
            page.goto(DOC_URL, wait_until="networkidle")
            
            # Wait for the text to actually appear on the page
            page.wait_for_selector("text=Berliner", timeout=15000)
            
            # Get all text from the document
            content = page.locator("body").inner_text()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            browser.close()
            
            results = []
            for park in MY_PARKS:
                for i, line in enumerate(lines):
                    # Partial match to be safe
                    if park.lower() in line.lower():
                        if i + 1 < len(lines):
                            status_text = lines[i+1]
                            
                            # Emoji Logic based on your image keywords
                            status_upper = status_text.upper()
                            if "SCHEDULED" in status_upper or "OPEN" in status_upper:
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
            return None # Trigger the 'unreachable' message if it fails

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    park_summary = get_park_data()
    
    if not park_summary:
        park_summary = "⚠️ **Update:** The city's status document is currently unreachable. [Check Manually](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"

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
