import requests
import csv
import os
from datetime import datetime
import pytz
import json

url = "https://oxide.sensibull.com/v1/compute/cache/fii_dii_daily"

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
    "Cookie": "sb_rudder_utm={}; rl_session=RudderEncrypt%3AU2FsdGVkX19kGEYrZWI%2F20GZ23bGjmGTn%2Bti%2FM3m2J5%2BuePDz%2B9DOyH4FkdZMLK8ZIqtW65HTH4%2Fg9Ve6cdAzXADy9HEctywCvvHU3rCXD0%2BLR6F2mvMqNvCtZ6amidBKsABVmEpFrBzL8wF1jIQHQ%3D%3D; rl_anonymous_id=RudderEncrypt%3AU2FsdGVkX1%2BQMHqC79%2Bnant6JC%2FCxq9Xv08jbUEOa7nJY4j3lQlF2qunHpnggi%2BQRc0fP8%2FJkGImIM6fJcve4A%3D%3D; rl_page_init_referrer=RudderEncrypt%3AU2FsdGVkX1%2BfkU80g4tOtuscysP1DmlqCrSJoHksnaQR75F6v33Bu226jyZQ7iu%2F; rl_page_init_referring_domain=RudderEncrypt%3AU2FsdGVkX19R%2BM4XZBn4Z55ALmtGn0WDIQd2elaJDrxThZ2741C%2Fk%2FpdKAkkLDPU; _ga_NC7XJTRTDX=GS2.1.s1784000989$o8$g0$t1784000989$j60$l0$h0; _ga=GA1.1.673390247.1776219026; bkd_ref=umR1rSNvX7Ef8guV; access_token=pa:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3ODQwNzk5MDAsImF1ZCI6InVhdXRoL3BsYXRmb3JtX2Fub24ifQ.NCqboDXJmpkmUrxEuSEgbGlsVkJubQblN8GqOHER-zw; _cfuvid=nMmJPyatz36Yi1tnRUuVhG7fO2mCg0w10omVjHjBsLI-1784001056.8831244-1.0.1.1-2CJY.v7XTlnaL9RpPl3WZXO4WBJdmke0FIB5ToiYuME; rl_user_id=RudderEncrypt%3AU2FsdGVkX1%2FFr4rcwqxa9uB3Ce0OON7259vdrTesCDg%3D; rl_trait=RudderEncrypt%3AU2FsdGVkX1%2BrCEZ%2FDYdcj8ZAsoxXnaeOejCadzPqbcATyGZSB7FRngRnCI3YJR0c",
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
