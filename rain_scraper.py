import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Configuration
# These must match the names on the website EXACTLY
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
MESSAGE_ID = os.getenv('MESSAGE_ID')

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        url = "https://columbusrecparks.com/facilities/rentals/sports/field-conditions/"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # We search specifically for the text of each park
        for park_name in MY_PARKS:
            # Find the specific text for the park name
            park_tag = soup.find(string=lambda t: park_name in t if t else False)
            
            if park_tag:
                # We move "forward" from the park name to find the status line
                # This ignores empty spaces and generic headers
                current = park_tag.find_next()
                status_text = "Status Not Found"
                
                # Check the next 3 elements for status keywords
                for _ in range(3):
                    if current:
                        txt = current.get_text(strip=True)
                        if any(word in txt for word in ["Open", "as scheduled", "CLOSED", "Closed"]):
                            status_text = txt
                            break
                        current = current.find_next()

                # Assign Emojis based on status
                if "Open" in status_text or "as scheduled" in status_text:
                    emoji = "🟢"
                elif "CLOSED" in status_text or "Closed" in status_text:
                    emoji = "🔴"
                else:
                    emoji = "🟡" # For Seasonal or TBD
                
                results.append(f"{emoji} **{park_name}**: {status_text}")
        
        return "\n".join(results) if results else "⚠️ No park data found."
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

# 2. Execution Logic
if __name__ == "__main__":
    park_summary = get_park_data()
    current_time = int(time.time())
    
    # Clean formatting for Discord
    content = (
        "🏟️ **LIVE C-BUS FIELD CONDITIONS**\n"
        f"Last Checked: <t:{current_time}:R>\n\n"
        f"{park_summary}\n\n"
        "🔗 [Official Status Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"
    )

    if MESSAGE_ID:
        # Update existing message
        patch_url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
        requests.patch(patch_url, json={"content": content})
    else:
        # Create first message
        post_url = f"{WEBHOOK_URL}?wait=true"
        r = requests.post(post_url, json={"content": content})
        if r.status_code == 200:
            print(f"FIRST RUN: Add this ID to your GitHub Secrets: {r.json()['id']}")
