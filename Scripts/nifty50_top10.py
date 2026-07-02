import requests
import pandas as pd
from datetime import datetime
import pytz
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
}

url = "https://www.nseindia.com/api/NextApi/apiClient/marketWatchApi?functionName=getIndicesData&symbol=NIFTY%2050"

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Check if request was successful
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    exit(1)
except ValueError as e:
    print(f"Error parsing JSON: {e}")
    exit(1)

target_symbols = [
    "RELIANCE",
    "HDFCBANK", 
    "BHARTIARTL",
    "TCS",
    "ICICIBANK",
    "SBIN",
    "INFY",
    "BAJFINANCE",
    "LT",
    "HINDUNILVR"
]

symbol_dict = {}

# FIX: Access the nested data correctly - data['data']['data']
# The API response has: {"data": {"aduCount": {...}, "data": [...]}}
if 'data' in data and 'data' in data['data']:
    items = data['data']['data']  # This is the array of stock data
else:
    print("Unexpected data structure")
    exit(1)

for item in items:
    symbol = item.get('symbol')
    
    if symbol in target_symbols:
        pchange = item.get('pChange')
        if pchange is not None:
            percent_change_str = f"{pchange}%"
        else:
            percent_change_str = ""
        
        symbol_dict[symbol] = {
            'Symbol': symbol,
            'LTP': item.get('lastPrice'),
            'Chng': item.get('change'),
            '%': percent_change_str,
            'Previous': item.get('previousClose'),
            'Yr Hi': item.get('yearHigh'),
            'Yr Lo': item.get('yearLow')
        }

records = []
for symbol in target_symbols:
    if symbol in symbol_dict:
        records.append(symbol_dict[symbol])

# Create directory if it doesn't exist
os.makedirs('Data', exist_ok=True)

df = pd.DataFrame(records)
filename = 'Data/nifty50_stocks_top10.csv'  # Fixed the path
df.to_csv(filename, index=False)

# Add timestamp row
ist = pytz.timezone('Asia/Kolkata')
timestamp = datetime.now(ist).strftime("%d-%b %H:%M")
with open(filename, 'a') as f:
    f.write(f',,,,,Update Time:,{timestamp}\n')

print("CSV created successfully!")
print(f"Data saved to {filename}")
