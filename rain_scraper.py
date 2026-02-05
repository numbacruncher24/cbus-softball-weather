import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Config - The parks you want to see
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
MESSAGE_ID = os.getenv('MESSAGE_ID') # Found in GitHub Secrets

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Fetch the Columbus Parks webpage
        response = requests.get("https://columbusrecparks.com/facilities/rentals/sports/field-conditions/", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # We loop through the page text and look for our specific parks
        page_text = soup.get_text(separator="\n")
        lines = [line.strip() for line in page_text.split("\n") if line.strip()]

        for park in MY_PARKS:
            for i, line in enumerate(lines):
                if park in line:
                    # The status text is usually the very next line
                    if i + 1 < len(lines):
                        status_text = lines[i+1]
                        
                        # Assign Emojis
                        if "Open" in status_text or "as scheduled" in status_text:
                            emoji = "🟢"
                        elif "CLOSED" in status_text or "Closed" in status_text:
                            emoji = "🔴"
                        else:
                            emoji = "🟡" # For TBD/Seasonal
                            
                        results.append(f"{emoji} **{park}**: {status_text}")
                    break 

        return "\n".join(results)
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

# 2. Execution Logic
# This part MUST come after the function definition above
if __name__ == "__main__":
    park_summary = get_park_data()
    
    # Create the final message with a live "Last Updated" timestamp
    current_time = int(time.time())
    content = (
        "🏟️ **LIVE C-BUS FIELD CONDITIONS**\n"
        f"Last Checked: <t:{current_time}:R>\n\n"
        f"{park_summary}\n\n"
        "🔗 [Official Status Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"
    )

    if MESSAGE_ID:
        # EDIT the existing dashboard message
        url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
        response = requests.patch(url, json={"content": content})
        print("Dashboard updated successfully.")
    else:
        # POST a brand new message (do this once to get your ID)
        url = f"{WEBHOOK_URL}?wait=true"
        response = requests.post(url, json={"content": content})
        new_id = response.json().get('id')
        print(f"FIRST RUN SUCCESSFUL!")
        print(f"Go to GitHub Secrets and add MESSAGE_ID with this value: {new_id}")
