import requests
from bs4 import BeautifulSoup
import os
import time

# List of parks to watch
MY_PARKS = ["Anheuser-Busch", "Cooper", "Lou Berliner", "Spindler Road"]

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # We go back to the main page - it's more stable
        url = "https://columbusrecparks.com/facilities/rentals/sports/field-conditions/"
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Get every single bit of text on the page
        all_text = soup.get_text(separator="\n")
        lines = [l.strip() for l in all_text.split("\n") if l.strip()]
        
        results = []
        for park in MY_PARKS:
            for i, line in enumerate(lines):
                if park.lower() in line.lower():
                    # Once we find the park name, the status is usually the next non-empty line
                    if i + 1 < len(lines):
                        status = lines[i+1]
                        
                        # Determine Emoji
                        if any(word in status.upper() for word in ["OPEN", "SCHEDULED", "YES"]):
                            emoji = "🟢"
                        elif "CLOSED" in status.upper() or "NO" in status.upper():
                            emoji = "🔴"
                        else:
                            emoji = "🟡"
                            
                        results.append(f"{emoji} **{park}**: {status}")
                    break 
        
        return "\n".join(results)
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    park_summary = get_park_data()
    
    # If the scraper STILL finds nothing, we send a clear warning
    if not park_summary:
        park_summary = "⚠️ **Update:** Currently checking for field status... No data found on the primary scan."

    content = (
        "🏟️ **LIVE FIELD CONDITIONS**\n"
        f"Last Checked: <t:{int(time.time())}:R>\n\n"
        f"{park_summary}"
    )

    if MESSAGE_ID:
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        # This will post the initial message and print the ID in your GitHub logs
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"NEW MESSAGE ID: {r.json()['id']}")
