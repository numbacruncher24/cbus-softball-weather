import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Target URL
GOOGLE_DOC_URL = "https://docs.google.com/document/d/e/2PACX-1vR_MOf-yqS0F8XnS7_T78f2_jWn9_n-u0_T78f2_jWn9_n-u0/pub?embedded=true"

MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(GOOGLE_DOC_URL, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Get all lines of text from the Google Doc
        lines = [line.get_text(strip=True) for line in soup.find_all(['span', 'p']) if line.get_text(strip=True)]
        
        print(f"DEBUG: Found {len(lines)} lines of text in the Google Doc.")
        if len(lines) > 0:
            print(f"DEBUG: First 5 lines seen: {lines[:5]}") # This tells us if we actually hit the Doc

        results = []
        for park in MY_PARKS:
            for i, text in enumerate(lines):
                if park.lower() in text.lower(): # Case-insensitive search
                    print(f"DEBUG: Found match for {park} on line {i}")
                    # Look at next few lines for status
                    for offset in range(1, 4):
                        if i + offset < len(lines):
                            status_candidate = lines[i + offset]
                            if any(word in status_candidate.upper() for word in ["OPEN", "CLOSED", "SCHEDULED"]):
                                emoji = "🟢" if "OPEN" in status_candidate.upper() or "SCHEDULED" in status_candidate.upper() else "🔴"
                                results.append(f"{emoji} **{park}**: {status_text}")
                                break
        return "\n".join(results)
    except Exception as e:
        print(f"ERROR during scrape: {e}")
        return ""

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')

    if not WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK secret is missing or empty!")
    
    park_summary = get_park_data()
    
    if not park_summary:
        print("ERROR: No park summary was generated. Scraper found nothing.")
        # We send a "Test" message just to confirm the Webhook works
        park_summary = "⚠️ Scraper found no updates. Check [Official Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"

    content = f"🏟️ **FIELD UPDATES**\n<t:{int(time.time())}:R>\n\n{park_summary}"
    
    # Attempt to send
    if MESSAGE_ID:
        res = requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        res = requests.post(f"{WEBHOOK_URL}", json={"content": content})
    
    print(f"DEBUG: Discord API responded with Status Code: {res.status_code}")
