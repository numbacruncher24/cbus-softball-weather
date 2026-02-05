import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Config - These must match the website text exactly
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

def get_field_status():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # We look for the park name, then find its "sibling" (the status text)
        for park in MY_PARKS:
            # Find the element containing the park name
            park_element = soup.find(string=lambda t: park in t if t else False)
            
            if park_element:
                # Get the next text block (which is the status)
                status_block = park_element.find_next()
                if status_block:
                    status_text = status_block.get_text(strip=True)
                    
                    # Choose Emoji
                    if "Open" in status_text or "as scheduled" in status_text:
                        emoji = "🟢"
                    elif "CLOSED" in status_text or "Closed" in status_text:
                        emoji = "🔴"
                    else:
                        emoji = "🟡" # For TBD or Seasonal updates
                        
                    results.append(f"{emoji} **{park}**: {status_text}")

        return "\n".join(results) if results else "⚠️ No matching parks found on site."
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

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


