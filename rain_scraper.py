import requests
from bs4 import BeautifulSoup
import os
import time

# 1. The DIRECT source of the field conditions data
SOURCE_URL = "https://docs.google.com/document/d/e/2PACX-1vT5K8nL7Bf1_fR_YJ-Xo-U0o5X8nL7Bf1_fR_YJ-Xo-U0o5X8/pub?embedded=true"

MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        # Request the Google Doc directly
        r = requests.get(SOURCE_URL, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Google Docs stores text in <span> tags within <p> tags
        all_text_elements = soup.find_all(['span', 'p'])
        lines = [el.get_text(strip=True) for el in all_text_elements if el.get_text(strip=True)]
        
        results = []
        for park in MY_PARKS:
            for i, text in enumerate(lines):
                # We use a partial match in case of weird formatting
                if park.lower() in text.lower():
                    # Look at the next few lines for keywords like "CLOSED" or "OPEN"
                    for offset in range(1, 4):
                        if i + offset < len(lines):
                            status_candidate = lines[i + offset]
                            status_upper = status_candidate.upper()
                            
                            if any(word in status_upper for word in ["OPEN", "CLOSED", "SCHEDULED"]):
                                emoji = "🟢" if "OPEN" in status_upper or "SCHEDULED" in status_upper else "🔴"
                                results.append(f"{emoji} **{park}**: {status_candidate}")
                                break
                    break # Stop looking for this park once found
        
        return "\n".join(results)
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    park_summary = get_park_data()
    
    # If the scraper still fails, it means the Google URL changed again
    if not park_summary:
        park_summary = "⚠️ **Update:** The city's status document is currently unreachable. [Check Manually](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"

    content = (
        "🏟️ **LIVE FIELD CONDITIONS**\n"
        f"Last Checked: <t:{int(time.time())}:R>\n\n"
        f"{park_summary}"
    )

    if MESSAGE_ID:
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"SUCCESS! New Message ID: {r.json()['id']}")
