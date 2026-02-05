import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Configuration
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
MESSAGE_ID = os.getenv('MESSAGE_ID')

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Get the page
        r = requests.get("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Convert the whole page into simple lines of text
        # This is the "Old Reliable" way
        lines = [line.strip() for line in soup.get_text(separator="\n").split("\n") if line.strip()]
        
        results = []
        for park in MY_PARKS:
            for i, line in enumerate(lines):
                # If we find the park name in a line
                if park in line:
                    # The status is almost always the very next line
                    if i + 1 < len(lines):
                        status_text = lines[i+1]
                        
                        # Set the emoji
                        if "Open" in status_text or "as scheduled" in status_text:
                            emoji = "🟢"
                        elif "CLOSED" in status_text or "Closed" in status_text:
                            emoji = "🔴"
                        else:
                            emoji = "🟡" # For TBD/Seasonal/Alerts
                            
                        results.append(f"{emoji} **{park}**: {status_text}")
                    break # Move to the next park in our list
        
        return "\n".join(results) if results else "⚠️ No park data found."
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

if __name__ == "__main__":
    park_summary = get_park_data()
    
    # Create the final message
    content = (
        "🏟️ **LIVE C-BUS FIELD CONDITIONS**\n"
        f"Last Checked: <t:{int(time.time())}:R>\n\n"
        f"{park_summary}\n\n"
        "🔗 [Official Status Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"
    )

    if MESSAGE_ID:
        # Edit existing dashboard
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        # Create first post
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"FIRST RUN SUCCESS! Add this ID to GitHub Secrets: {r.json()['id']}")
