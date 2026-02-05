import time
import requests
from bs4 import BeautifulSoup
import os

# 1. Config
URL = "https://columbusrecparks.com/facilities/rentals/sports/field-conditions/"
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
# You'll get this ID after the first run (see instructions below)
MESSAGE_ID = os.getenv('MESSAGE_ID') 

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(URL, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        updates = []
        # Target the sports parks specifically
        for item in soup.find_all(['li', 'tr']):
            txt = item.get_text(strip=True)
            if any(p in txt for p in ["Berliner", "Busch", "Kilbourne", "Spindler", "Antrim"]):
                status = "🟢 **OPEN**" if "Open" in txt else "🔴 **CLOSED**"
                name = txt.split(" - ")[0]
                updates.append(f"{status} | {name}")
        return "\n".join(updates)
    except:
        return "⚠️ Error fetching data."

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
