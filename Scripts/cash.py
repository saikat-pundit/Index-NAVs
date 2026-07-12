import requests
import csv
import os
from datetime import datetime
import pytz

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
    "Cookie": "sb_rudder_utm={}; rl_session=RudderEncrypt%3AU2FsdGVkX18fecFqqTA6ZfR2GWvP77UStA8nklhswZhXgqMqtqtPsUOQla%2BoAEHtDb4ob%2BnNnaoQrucNa8j9nBoniVXWoSgLKp7RYhQMboD0RERgvIeFxZsdbA0PGhMdISTg3ftrkbzdQZ%2B6RbzBhQ%3D%3D; rl_anonymous_id=RudderEncrypt%3AU2FsdGVkX1%2FJhcVrQmy%2FMUSwccIu%2FwxMN2m5aN7Mzp6nO%2FKGDJdmDrzTE1PeCwfkVr22xkbcnPvvqTh56cAn4w%3D%3D; rl_page_init_referrer=RudderEncrypt%3AU2FsdGVkX1%2BfkU80g4tOtuscysP1DmlqCrSJoHksnaQR75F6v33Bu226jyZQ7iu%2F; rl_page_init_referring_domain=RudderEncrypt%3AU2FsdGVkX19R%2BM4XZBn4Z55ALmtGn0WDIQd2elaJDrxThZ2741C%2Fk%2FpdKAkkLDPU; _ga_NC7XJTRTDX=GS2.1.s1783864628$o6$g1$t1783864655$j33$l0$h0; _ga=GA1.1.673390247.1776219026; _cfuvid=GDr5SqtPCSGGoVr5hKzHMQZbQrTWVnCI_FwbR2rh8kA-1783864657967-0.0.1.1-604800000; access_token=pa:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3ODM5MDcxMDAsImF1ZCI6InVhdXRoL3BsYXRmb3JtX2Fub24ifQ.1qDa1JOzCqZUDg5K1i2MP-e0K4YIscqsBCdnV6fOhxo; bkd_ref=0qHcTcNTZFkft8z6; rl_user_id=RudderEncrypt%3AU2FsdGVkX19jyd3BL5k%2FuusB0hTb10eoTyiQKOR0Vhw%3D; rl_trait=RudderEncrypt%3AU2FsdGVkX19WV5Yd%2BQgm3qCSTvb%2FzQ8FytT%2FtcuoFnqQEE4f%2B4T2qPFaijdNkHey",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "TE": "trailers"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    data = response.json()
    print("Data fetched successfully!")
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    exit(1)
except ValueError as e:
    print(f"Error parsing JSON: {e}")
    print(f"Response text: {response.text[:200]}...")  # Print first 200 chars of response
    exit(1)

os.makedirs("Data", exist_ok=True)

with open("Data/Cash.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "FII Net Buy/Sell", "DII Net Buy/Sell"])
    
    # Check if data exists in the expected format
    if "data" not in data:
        print("Warning: 'data' key not found in response")
        print(f"Available keys: {list(data.keys())}")
        sorted_dates = []
    else:
        sorted_dates = sorted(data["data"], reverse=True)
    
    for date_str in sorted_dates:
        day = data["data"][date_str]
        if "cash" in day:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d %b %y")
                
                fii_val = int(day["cash"]["fii"]["buy_sell_difference"])
                dii_val = int(day["cash"]["dii"]["buy_sell_difference"])
                
                writer.writerow([formatted_date, f"{fii_val} Cr.", f"{dii_val} Cr."])
            except (KeyError, ValueError, TypeError) as e:
                print(f"Error processing date {date_str}: {e}")
                continue
    
    # Add timestamp row with IST
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime("%d %b %H:%M")
    writer.writerow(["", "Update Time:", timestamp])

print(f"Data written to Data/Cash.csv successfully!")
