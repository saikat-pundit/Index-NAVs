import requests
import pandas as pd
import os
import pytz
from datetime import datetime, timedelta
import json

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
    "Cookie": "sb_rudder_utm={}; rl_session=RudderEncrypt%3AU2FsdGVkX19kGEYrZWI%2F20GZ23bGjmGTn%2Bti%2FM3m2J5%2BuePDz%2B9DOyH4FkdZMLK8ZIqtW65HTH4%2Fg9Ve6cdAzXADy9HEctywCvvHU3rCXD0%2BLR6F2mvMqNvCtZ6amidBKsABVmEpFrBzL8wF1jIQHQ%3D%3D; rl_anonymous_id=RudderEncrypt%3AU2FsdGVkX1%2BQMHqC79%2Bnant6JC%2FCxq9Xv08jbUEOa7nJY4j3lQlF2qunHpnggi%2BQRc0fP8%2FJkGImIM6fJcve4A%3D%3D; rl_page_init_referrer=RudderEncrypt%3AU2FsdGVkX1%2BfkU80g4tOtuscysP1DmlqCrSJoHksnaQR75F6v33Bu226jyZQ7iu%2F; rl_page_init_referring_domain=RudderEncrypt%3AU2FsdGVkX19R%2BM4XZBn4Z55ALmtGn0WDIQd2elaJDrxThZ2741C%2Fk%2FpdKAkkLDPU; _ga_NC7XJTRTDX=GS2.1.s1784000989$o8$g0$t1784000989$j60$l0$h0; _ga=GA1.1.673390247.1776219026; bkd_ref=umR1rSNvX7Ef8guV; access_token=pa:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3ODQwNzk5MDAsImF1ZCI6InVhdXRoL3BsYXRmb3JtX2Fub24ifQ.NCqboDXJmpkmUrxEuSEgbGlsVkJubQblN8GqOHER-zw; _cfuvid=nMmJPyatz36Yi1tnRUuVhG7fO2mCg0w10omVjHjBsLI-1784001056.8831244-1.0.1.1-2CJY.v7XTlnaL9RpPl3WZXO4WBJdmke0FIB5ToiYuME; rl_user_id=RudderEncrypt%3AU2FsdGVkX1%2FFr4rcwqxa9uB3Ce0OON7259vdrTesCDg%3D; rl_trait=RudderEncrypt%3AU2FsdGVkX1%2BrCEZ%2FDYdcj8ZAsoxXnaeOejCadzPqbcATyGZSB7FRngRnCI3YJR0c",
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
