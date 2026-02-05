import requests
from bs4 import BeautifulSoup
import os
import time

# 1. Target the Google Doc Source directly
# This is the secret URL where the actual data lives
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
        # We request the Google Doc directly
        r = requests.get(GOOGLE_DOC_URL, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Google Docs format text into simple <span> or <p> tags
        lines = [line.get_text(strip=True) for line in soup.find_all(['span', 'p']) if line.get_text(strip=True)]
        
        results = []
        for park in MY_PARKS:
            for i, text in enumerate(lines):
                if park in text:
                    # Look at the next few lines for the status
                    # (Google Docs often split lines oddly)
                    for offset in range(1, 4):
                        if i + offset < len(lines):
                            status_candidate = lines[i + offset]
                            if any(word in status_candidate.upper() for word in ["OPEN", "CLOSED", "SCHEDULED"]):
                                emoji = "🟢" if "OPEN" in status_candidate.upper() or "SCHEDULED" in status_candidate.upper() else "🔴"
                                results.append(f"{emoji} **{park}**: {status_candidate}")
                                break
                    break
        
        return "\n".join(results) if results else "⚠️ No park data found in Google Doc."
    except Exception as e:
        return f"⚠️ Scraper Error: {e}"

# ... The rest of your execution logic (Webhook, Message ID) remains the same ...
