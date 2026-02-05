import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Config
URL = "https://columbusrecparks.com/facilities/rentals/sports/field-conditions/"
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
# You'll get this ID after the first run (see instructions below)
MESSAGE_ID = os.getenv('MESSAGE_ID') 

import requests
from bs4 import BeautifulSoup
import time

# 1. Exact list from your screenshot
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        updates = []
        
        # We loop through the page text and look for our specific parks
        page_text = soup.get_text(separator="\n")
        lines = [line.strip() for line in page_text.split("\n") if line.strip()]

        for park in MY_PARKS:
            for i, line in enumerate(lines):
                if park in line:
                    # The status is usually the very next line on this website
                    if i + 1 < len(lines):
                        status_text = lines[i+1]
                        
                        # Set Emojis based on status keywords
                        if "Open" in status_text or "as scheduled" in status_text:
                            emoji = "🟢"
                        elif "Closed" in status_text or "CLOSED" in status_text:
                            emoji = "🔴"
                        else:
                            emoji = "🟡" # For "TBD" or "Delayed"
                            
                        updates.append(f"{emoji} **{park}**: {status_text}")
                    break # Stop looking for this park once found

        return "\n".join(updates)
    except Exception as e:
        return f"⚠️ Error: {e}"

# 2. Prepare Payload
content = f"🏟️ **LIVE C-BUS FIELD CONDITIONS**\n*Last Updated: <t:{int(time.time())}:R>*\n\n{get_park_data()}\n\n🔗 [Official Page]({URL})"

# 3. Send or Edit
if MESSAGE_ID:
    # EDIT existing message
    edit_url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
    requests.patch(edit_url, json={"content": content})
else:
    # POST new message (do this once to get your ID)
    r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})

    print(f"FIRST RUN: Copy this ID and add it to GitHub Secrets as MESSAGE_ID: {r.json()['id']}")

