import requests
import pandas as pd
import os
import pytz
from datetime import datetime, timedelta
import json

# Get cookie from Data/cookie.txt
try:
    with open('Data/cookie.txt', 'r') as f:
        COOKIE = f.read().strip()
    if not COOKIE:
        print("ERROR: Data/cookie.txt is empty!")
        exit(1)
except FileNotFoundError:
    print("ERROR: Data/cookie.txt not found!")
    exit(1)
    
# Complete headers from the request
headers = {
    "Host": "oxide.sensibull.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://web.sensibull.com/",
    "Content-Type": "application/json",
    "frt-ref": "k843p8v2ie",
    "x-device-id": "749e28d9-7b8b-4947-9b7e-3700a492c4bd",
    "Origin": "https://web.sensibull.com",
    "DNT": "1",
    "Connection": "keep-alive",
    "Cookie": COOKIE,  # Using environment variable
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "TE": "trailers"
}

today = datetime.now()
payload = {
    "from_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
    "to_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
    "countries": ["India", "China", "Japan", "Euro Area", "USA"],
    "impacts": []
}

def impact_to_stars(impact):
    """Convert impact level to star rating"""
    if not impact:
        return ""
    impact_lower = impact.lower()
    if "high" in impact_lower:
        return "★★★"
    elif "medium" in impact_lower:
        return "★★"
    elif "low" in impact_lower:
        return "★"
    return impact.capitalize()

try:
    print("Fetching economic data from API...")
    response = requests.post(
        "https://oxide.sensibull.com/v1/compute/market_global_events",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"Response Status Code: {response.status_code}")
    response.raise_for_status()
    
    # Parse JSON response
    try:
        data = response.json()
        print("JSON parsed successfully!")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        data = {"success": False}
        
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status: {e.response.status_code}")
        print(f"Response text: {e.response.text[:500]}")
    data = {"success": False}

# Debug: Check response structure
print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")

# Extract data from response
raw_data = []
if data.get('success', False):
    raw_data = data.get('payload', {}).get('data', [])
    print(f"Found {len(raw_data)} economic events")
else:
    print("Warning: API returned success=False or missing data")
    # Try alternate data extraction if needed
    if 'payload' in data:
        raw_data = data.get('payload', {}).get('data', [])
        print(f"Found {len(raw_data)} events in payload")
    elif 'data' in data:
        raw_data = data.get('data', [])
        print(f"Found {len(raw_data)} events in root data")

# Process records
records = []
for idx, item in enumerate(raw_data):
    try:
        date_str = item.get('date', '')
        if date_str:
            try:
                formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b")
            except ValueError:
                formatted_date = date_str
        else:
            formatted_date = ""
        
        area = item.get('country', '')
        if area == "Euro Area":
            area = "Euro"
        
        # Get time and truncate to HH:MM
        time_str = item.get('time', '')
        if time_str and len(time_str) >= 5:
            time_str = time_str[:5]
        
        records.append({
            'Date': formatted_date,
            'Time': time_str,
            'Area': area,
            'Title': item.get('title', ''),
            'Imp.': impact_to_stars(item.get('impact', '')),
            'Actual': item.get('actual', ''),
            'Exp.': item.get('expected', ''),
            'Prev.': item.get('previous', '')
        })
    except Exception as e:
        print(f"Error processing item {idx}: {e}")
        continue

# Add update timestamp
records.append({
    'Date': '',
    'Time': '',
    'Area': '',
    'Title': '',
    'Imp.': '',
    'Actual': '',
    'Exp.': 'Update Time:',
    'Prev.': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%b %H:%M')
})

# Create Data directory
os.makedirs('Data', exist_ok=True)

# Save to CSV
df = pd.DataFrame(records)
df.to_csv('Data/Economic.csv', index=False)

print(f"Data saved to Data/Economic.csv successfully! ({len(records)-1} events)")
print(f"Sample records: {records[:2] if records else 'No records'}")
