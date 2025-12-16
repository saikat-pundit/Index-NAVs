import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
}

# Specific funds to fetch (with full names for API matching)
target_funds_api = [
    "Aditya Birla Sun Life PSU Equity Fund-Direct Plan-Growth",
    "Axis Focused Fund - Direct Plan - Growth Option",
    "Axis Large & Mid Cap Fund - Direct Plan - Growth",
    "Axis Large Cap Fund - Direct Plan - Growth",
    "Axis Small Cap Fund - Direct Plan - Growth",
    "ICICI Prudential Banking and PSU Debt Fund - Direct Plan -  Growth",
    "ICICI Prudential Corporate Bond Fund - Direct Plan - Growth",
    "ICICI Prudential Gilt Fund - Direct Plan - Growth",
    "ICICI Prudential Nifty 50 Index Fund - Direct Plan Cumulative Option",
    "ICICI PRUDENTIAL SILVER ETF FUND OF FUND - Direct Plan - Growth",
    "ICICI Prudential Technology Fund - Direct Plan -  Growth",
    "Mahindra Manulife Consumption Fund - Direct Plan -Growth",
    "Mirae Asset Arbitrage Fund Direct Growth",
    "Mirae Asset ELSS Tax Saver Fund - Direct Plan - Growth",
    "Mirae Asset Healthcare Fund Direct Growth",
    "Nippon India Gold Savings Fund - Direct Plan Growth Plan - Growth Option",
    "Nippon India Nifty Next 50 Junior BeES FoF - Direct Plan - Growth Plan - Growth Option",
    "Nippon India Nivesh Lakshya Long Duration Fund- Direct Plan- Growth Option",
    "quant ELSS Tax Saver Fund - Growth Option - Direct Plan",
    "SBI MAGNUM GILT FUND - DIRECT PLAN - GROWTH"
]

# Function to extract display name (everything before first dash)
def extract_display_name(full_name):
    # Split by dash and take the first part, strip whitespace
    display_name = full_name.split('-')[0].strip()
    # If there are multiple spaces, collapse them to single space
    display_name = ' '.join(display_name.split())
    return display_name

# Create display names for CSV
display_names = [extract_display_name(fund) for fund in target_funds_api]

# Create a mapping from display name to API name for lookup
fund_name_mapping = dict(zip(display_names, target_funds_api))

# Set IST timezone
ist = pytz.timezone('Asia/Kolkata')

# Get the correct date in IST
today = datetime.now(ist)  # Use IST timezone
# If today is Monday, go back to Friday (3 days)
if today.weekday() == 0:  # Monday = 0
    target_date = today - timedelta(days=3)
# If today is Sunday, go back to Friday (2 days)
elif today.weekday() == 6:  # Sunday = 6
    target_date = today - timedelta(days=2)
# For other days, use previous day
else:
    target_date = today - timedelta(days=1)

target_date_str = target_date.strftime('%Y-%m-%d')
url = f"https://www.amfiindia.com/api/nav-history?query_type=all_for_date&from_date={target_date_str}"

response = requests.get(url, headers=headers)
data = response.json()

# Create a dictionary to store NAV data for quick lookup
nav_data = {}

for fund in data['data']:
    for scheme in fund['schemes']:
        for nav in scheme['navs']:
            nav_name = nav['NAV_Name']
            
            # Check if this NAV is in our target list
            if nav_name in target_funds_api:
                # Extract display name
                display_name = extract_display_name(nav_name)
                nav_data[display_name] = {
                    'Fund NAV': nav['hNAV_Amt'],
                    'Update Time': nav['hNAV_Upload_display']
                }

# Prepare records in the order of display_names
sorted_records = []
funds_found = 0

for display_name in display_names:
    # Check if we have data for this fund
    if display_name in nav_data:
        sorted_records.append({
            'Fund Name': display_name,
            'Fund NAV': nav_data[display_name]['Fund NAV'],
            'Update Time': nav_data[display_name]['Update Time']
        })
        funds_found += 1
    else:
        # If fund not found, show '-'
        sorted_records.append({
            'Fund Name': display_name,
            'Fund NAV': '-',
            'Update Time': '-'
        })

# Add timestamp row with IST
timestamp = datetime.now(ist).strftime('%d-%b-%Y %H:%M')
sorted_records.append({
    'Fund Name': '',
    'Fund NAV': 'Last Updated:',
    'Update Time': f'{timestamp} IST'
})

# Save to CSV
os.makedirs('Data', exist_ok=True)
df = pd.DataFrame(sorted_records)
df.to_csv('Data/Daily_NAV.csv', index=False)

print(f"NAV data saved successfully for date: {target_date_str}!")
print(f"Funds found: {funds_found} out of {len(display_names)}")
print(f"Timestamp: {timestamp} IST")
print(f"File saved to: Data/Daily_NAV.csv")

# Display sample of how names appear in CSV
print("\nSample of fund names in CSV:")
print("=" * 50)
for i, record in enumerate(sorted_records[:5]):  # Show first 5
    if record['Fund Name']:  # Skip the timestamp row
        print(f"{record['Fund Name']} - NAV: {record['Fund NAV']}")
print("=" * 50)
