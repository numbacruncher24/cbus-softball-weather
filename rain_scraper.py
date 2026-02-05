import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Direct Published URL (Found by inspecting the website's iframe)
SOURCE_URL = "https://docs.google.com/document/d/e/2PACX-1vT5K8nL7Bf1_fR_YJ-Xo-U0o5X8nL7Bf1_fR_YJ-Xo-U0o5X8/pub?embedded=true"

# The 4 parks from your image
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Request the Google Doc directly
        response = requests.get(SOURCE_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Google Docs often separate text into many small <span> tags
        lines = [el.get_text(strip=True) for el in soup.find_all(['span', 'p']) if el.get_text(strip=True)]
        
        results = []
        for park in MY_PARKS:
            for i, text in enumerate(lines):
                # We check for a case-insensitive match
                if park.lower() in text.lower():
                    # Status is usually 1-3 lines below the park name in the code
                    for offset in range(1, 4):
                        if i + offset < len(lines):
                            status_val = lines[i + offset]
                            status_upper = status_val.upper()
                            
                            # Filter for actual status keywords
                            if any(word in status_upper for word in ["OPEN", "CLOSED", "SCHEDULED", "SEASON"]):
                                emoji = "🟢" if "OPEN" in status_upper or "SCHEDULED" in status_upper else "🔴"
                                results.append(f"{emoji} **{park}**: {status_val}")
                                break
                    break # Stop looking for this park once found
        
        return "\n".join(results)
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

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
