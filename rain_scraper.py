import os
import time
from playwright.sync_api import sync_playwright

MY_PARKS = ["Anheuser-Busch", "Cooper", "Lou Berliner", "Spindler Road"]

def get_park_data():
    with sync_playwright() as p:
        # Launch a "headless" browser (no window pops up)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Go to the main parks page
        page.goto("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", wait_until="networkidle")
        
        # Give the Google Doc an extra 5 seconds to load inside the frame
        time.sleep(5)
        
        # Grab all the text the browser currently "sees"
        full_text = page.content() 
        
        # Close browser
        browser.close()
        
        results = []
        # Simple search in the raw text for your status updates
        lines = full_text.split("\n")
        for park in MY_PARKS:
            if park in full_text:
                # This is a broad search for the status right after the park name
                # You can refine this logic once we see the first output!
                results.append(f"🔍 Found data for {park}...")

        return "\n".join(results) if results else "⚠️ Browser couldn't find the parks."


# Execution Logic (Webhook & Message ID) remains the same as your original
if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    park_summary = get_park_data()
    
    if not park_summary:
        park_summary = "⚠️ **Update:** No status data found in the current source. [Check Manually](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"

    content = f"🏟️ **FIELD CONDITIONS**\nLast Checked: <t:{int(time.time())}:R>\n\n{park_summary}"

    if MESSAGE_ID:
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"NEW MESSAGE ID: {r.json()['id']}")

