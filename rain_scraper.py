import os
import time
import requests
from bs4 import BeautifulSoup

# The 4 parks from your image
MY_PARKS = [
    "Anheuser-Busch",
    "Cooper",
    "Berliner",
    "Spindler"
]

# Your specific Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTt2lqkwmk7MgbpvKaI3H1GiQVDFfyNOyKNM9Yri13LHDxhlCzVDvd-AdvejoxsB2mZHyUIMQkjlpxK/pubhtml?widget=true&headers=false"

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(SHEET_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Grab every single table cell in the sheet
        cells = [td.get_text(strip=True) for td in soup.find_all('td')]
        
        results = []
        for park in MY_PARKS:
            for i, cell_text in enumerate(cells):
                if park.lower() in cell_text.lower():
                    # We found the park! Now look at the next 10 cells 
                    # to find the status (Open/Closed/Scheduled)
                    found_status = False
                    for offset in range(1, 11):
                        if i + offset < len(cells):
                            status_candidate = cells[i + offset]
                            status_upper = status_candidate.upper()
                            
                            if any(word in status_upper for word in ["OPEN", "CLOSED", "SCHEDULED", "SEASON"]):
                                emoji = "🟢" if "OPEN" in status_upper or "SCHEDULED" in status_upper else "🔴"
                                results.append(f"{emoji} **{park}**: {status_candidate}")
                                found_status = True
                                break
                    if found_status: break
        
        return "\n".join(results)
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    park_summary = get_park_data()
    
    if not park_summary:
        park_summary = "⚠️ **Update:** Successfully connected to the sheet, but no park statuses were found in the current view."

    content = (
        "🏟️ **LIVE FIELD CONDITIONS**\n"
        f"Last Checked: <t:{int(time.time())}:R>\n\n"
        f"{park_summary}\n\n"
        "🔗 [Official Status Page](https://columbusrecparks.com/facilities/rentals/sports/field-conditions/)"
    )

    if MESSAGE_ID:
        requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json={"content": content})
    else:
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json={"content": content})
        if r.status_code == 200:
            print(f"SUCCESS! New Message ID: {r.json()['id']}")
