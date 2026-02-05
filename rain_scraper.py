import os
import time
import requests
from bs4 import BeautifulSoup

# The 4 parks from your image
MY_PARKS = [
    "Anheuser-Busch Sports Park",
    "Cooper Sports Park",
    "Lou Berliner Sports Park",
    "Spindler Road Park"
]

# The NEW Google Sheets URL you provided
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTt2lqkwmk7MgbpvKaI3H1GiQVDFfyNOyKNM9Yri13LHDxhlCzVDvd-AdvejoxsB2mZHyUIMQkjlpxK/pubhtml?widget=true&headers=false"

def get_park_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(SHEET_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Google Sheets published as HTML use <td> tags for cells
        cells = [td.get_text(strip=True) for td in soup.find_all('td')]
        
        results = []
        for park in MY_PARKS:
            for i, cell_text in enumerate(cells):
                if park.lower() in cell_text.lower():
                    # In this specific sheet, the status is usually in the cell directly below 
                    # or next to the park name. We'll look at the next 2 cells.
                    for offset in range(1, 3):
                        if i + offset < len(cells):
                            status_candidate = cells[i + offset]
                            status_upper = status_candidate.upper()
                            
                            if any(word in status_upper for word in ["OPEN", "CLOSED", "SCHEDULED", "SEASON"]):
                                emoji = "🟢" if "OPEN" in status_upper or "SCHEDULED" in status_upper else "🔴"
                                results.append(f"{emoji} **{park}**: {status_candidate}")
                                break
                    break
        
        return "\n".join(results)
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

if __name__ == "__main__":
    WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
    MESSAGE_ID = os.getenv('MESSAGE_ID')
    
    park_summary = get_park_data()
    
    if not park_summary:
        park_summary = "⚠️ **Update:** Field data found, but status keywords were missing."

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
