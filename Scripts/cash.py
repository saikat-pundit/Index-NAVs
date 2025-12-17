import requests
import csv
import os
from datetime import datetime

url = "https://oxide.sensibull.com/v1/compute/cache/fii_dii_daily"
headers = {'User-Agent': 'Mozilla/5.0'}

response = requests.get(url, headers=headers)
response.raise_for_status()
data = response.json()

output_dir = "Data"
os.makedirs(output_dir, exist_ok=True)
csv_file = os.path.join(output_dir, "Cash.csv")

with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "FII buy_sell_difference", "DII buy_sell_difference"])
    
    for date_str in sorted(data["data"]):
        daily_data = data["data"][date_str]
        if "cash" in daily_data and "fii" in daily_data["cash"] and "dii" in daily_data["cash"]:
            fii_diff = daily_data["cash"]["fii"]["buy_sell_difference"]
            dii_diff = daily_data["cash"]["dii"]["buy_sell_difference"]
            writer.writerow([date_str, fii_diff, dii_diff])
