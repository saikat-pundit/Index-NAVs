import requests
import pandas as pd
from datetime import datetime
import pytz
import os

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

urls = {
    "Today": "https://www.moneycontrol.com/economic-widget?duration=T&startDate=&endDate=&impact=&country=&deviceType=web&classic=true",
    "Tomorrow": "https://www.moneycontrol.com/economic-widget?duration=TO&startDate=&endDate=&impact=&country=&deviceType=web&classic=true"
}

def format_time(timestamp):
    try:
        utc_time = datetime.utcfromtimestamp(int(timestamp))
        ist = pytz.timezone('Asia/Kolkata')
        return pytz.utc.localize(utc_time).astimezone(ist).strftime('%H:%M')
    except:
        return ""

def clean_value(value):
    if isinstance(value, str):
        return value.replace('%', '')
    return value

def get_country_name(code):
    countries = {
        'JPN': 'Japan', 'CHN': 'China', 'KOR': 'South Korea',
        'SAU': 'Saudi Arabia', 'IND': 'India', 'TUR': 'Turkey',
        'DEU': 'Germany', 'ZAF': 'South Africa', 'EUR': 'Euro Area',
        'BRA': 'Brazil', 'CAN': 'Canada', 'USA': 'United States',
        'FRA': 'France'
    }
    return countries.get(code, code)

def fetch_data():
    records = []
    
    for period, url in urls.items():
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for item in data['data']:
                        trend = item.get('trend', '')
                        trend_symbol = '↑' if trend == 'up' else '↓' if trend == 'down' else '-'
                        
                        records.append({
                            'Time': format_time(item.get('datetime')),
                            'Country': get_country_name(item.get('country', '')),
                            'Indicator': item.get('indicator', '').strip(),
                            'Actual': clean_value(item.get('actual', '')),
                            'Forecast': clean_value(item.get('forecast', '')),
                            'Previous': clean_value(item.get('previous', '')),
                            'Impact': item.get('impact', '').capitalize(),
                            'Trend': trend_symbol
                        })
        except:
            continue
    
    if not records:
        current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%b %H:%M')
        records.append({
            'Time': '', 'Country': 'No Data', 'Indicator': '',
            'Actual': '', 'Forecast': '', 'Previous': '',
            'Impact': '', 'Trend': f'Last checked: {current_time}'
        })
    
    # Add timestamp
    current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%b %H:%M')
    records.append({
        'Time': '', 'Country': '', 'Indicator': '',
        'Actual': '', 'Forecast': '', 'Previous': '',
        'Impact': 'Updated', 'Trend': current_time
    })
    
    return pd.DataFrame(records)

# Main execution
os.makedirs('Data', exist_ok=True)
df = fetch_data()
df.to_csv('Data/Economic.csv', index=False)
