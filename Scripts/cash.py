import requests
import csv
import os
from datetime import datetime
import pytz
import json

url = "https://oxide.sensibull.com/v1/compute/cache/fii_dii_daily"

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

headers = {
    "Host": "oxide.sensibull.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://web.sensibull.com/",
    "frt-ref": "fjwv4v2ofl",
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

try:
    print("Fetching data from API...")
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    # Check if response is successful
    response.raise_for_status()
    
    # Try to parse JSON
    try:
        data = response.json()
        print("JSON parsed successfully!")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status: {e.response.status_code}")
        print(f"Response text: {e.response.text[:500]}")
    exit(1)

# Debug: Print the structure of the response
print(f"Response keys: {list(data.keys())}")

# Check if 'data' key exists
if "data" not in data:
    print("ERROR: 'data' key not found in response!")
    print(f"Available keys: {list(data.keys())}")
    print(f"Full response: {json.dumps(data, indent=2)[:1000]}...")
    exit(1)

# Check if 'data' is a dictionary
if not isinstance(data["data"], dict):
    print(f"ERROR: 'data' is not a dictionary, it's {type(data['data'])}")
    print(f"Data: {data['data']}")
    exit(1)

print(f"Number of dates in data: {len(data['data'])}")
print(f"Sample dates: {list(data['data'].keys())[:5]}")

# Create Data directory
os.makedirs("Data", exist_ok=True)

# Write to CSV
with open("Data/Cash.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "FII Net Buy/Sell", "DII Net Buy/Sell"])
    
    sorted_dates = sorted(data["data"].keys(), reverse=True)
    print(f"Processing {len(sorted_dates)} dates...")
    
    row_count = 0
    for date_str in sorted_dates:
        day = data["data"][date_str]
        
        # Check if 'cash' data exists for this date
        if "cash" not in day:
            print(f"Warning: No 'cash' data for {date_str}")
            continue
            
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %b %y")
            
            # Extract FII and DII values
            fii_val = int(day["cash"]["fii"]["buy_sell_difference"])
            dii_val = int(day["cash"]["dii"]["buy_sell_difference"])
            
            writer.writerow([formatted_date, f"{fii_val} Cr.", f"{dii_val} Cr."])
            row_count += 1
            
        except KeyError as e:
            print(f"Error: Missing key {e} for date {date_str}")
            print(f"Available cash keys: {list(day['cash'].keys()) if 'cash' in day else 'No cash data'}")
            continue
        except ValueError as e:
            print(f"Error converting value for {date_str}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error for {date_str}: {e}")
            continue
    
    print(f"Successfully wrote {row_count} rows to CSV")
    
    # Add timestamp row with IST
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime("%d %b %H:%M")
    writer.writerow(["", "Update Time:", timestamp])

print("Data saved to Data/Cash.csv successfully!")
