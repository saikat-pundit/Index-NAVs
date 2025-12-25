import requests
import pandas as pd
from datetime import datetime, timedelta, time, date
import pytz
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from iv_calculator import CalcIvGreeks, TryMatchWith

# Define holidays
HOLIDAYS = [
    "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
    "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
    "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
    "2025-11-05", "2025-12-25", "2026-01-26", "2026-03-03", 
    "2026-03-26", "2026-03-31", "2026-04-03", "2026-04-14", 
    "2026-05-01", "2026-05-28", "2026-06-26", "2026-09-14", 
    "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-24", 
    "2026-12-25"
]

# Convert holiday strings to date objects for easier comparison
HOLIDAY_DATES = [datetime.strptime(holiday, "%Y-%m-%d").date() for holiday in HOLIDAYS]

def is_market_day():
    """Check if current day is a trading day (weekday and not a holiday)"""
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = datetime.now(ist)
    current_date = ist_now.date()
    
    # Check if it's a weekend
    if ist_now.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False
    
    # Check if it's a holiday
    if current_date in HOLIDAY_DATES:
        return False
    
    return True

def is_market_hours():
    """Check if current time is within market hours (IST: 9:15 AM to 3:40 PM)"""
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = datetime.now(ist)
    
    # First check if it's a market day
    if not is_market_day():
        return False
    
    # Get current time
    current_time = ist_now.time()
    
    # Define market hours with buffer
    market_open = time(9, 15)   # 9:15 AM (15 mins buffer)
    market_close = time(15, 40) # 3:40 PM (10 mins buffer)
    
    # Check if within market hours (inclusive)
    return market_open <= current_time <= market_close

def get_market_status_message():
    """Get detailed message about why market is closed"""
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = datetime.now(ist)
    current_date = ist_now.date()
    current_time_str = ist_now.strftime('%Y-%m-%d %H:%M:%S IST')
    weekday = ist_now.strftime('%A')
    
    # Check weekend
    if ist_now.weekday() >= 5:
        return f"Market closed - {weekday} (Weekend)", False
    
    # Check holiday
    if current_date in HOLIDAY_DATES:
        # Find holiday name if available in original list
        holiday_str = ""
        for holiday in HOLIDAYS:
            if holiday.startswith(str(current_date)):
                holiday_str = f" ({holiday})"
                break
        return f"Market closed - {weekday}{holiday_str} (Holiday)", False
    
    # Check market hours
    market_open = time(9, 15)
    market_close = time(15, 40)
    current_time = ist_now.time()
    
    if current_time < market_open:
        time_to_open = datetime.combine(current_date, market_open) - datetime.combine(current_date, current_time)
        hours, remainder = divmod(time_to_open.seconds, 3600)
        minutes = remainder // 60
        return f"Market opens in {hours}h {minutes}m at 9:15 AM", False
    
    if current_time > market_close:
        return f"Market closed at 3:30 PM today", False
    
    return f"Market open - {weekday}", True

def main():
    # Get market status with detailed message
    status_message, is_open = get_market_status_message()
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')
    
    print(f"Current time: {current_time}")
    print(f"Status: {status_message}")
    
    # Exit if market is not open
    if not is_open:
        print("Script not running - outside trading hours")
        print("Exiting...")
        return
    
    # Continue with the rest of the script only if market is open
    print("Fetching option chain data...")
    
    expiry_date = get_next_tuesday()
    
    data, expiry = get_option_chain(expiry=expiry_date)
    
    if data:
        df = create_option_chain_dataframe(data, expiry)
        os.makedirs('Data', exist_ok=True)
        
        output_file = 'Data/Option.csv'
        df.to_csv(output_file, index=False)
        
        current_time = datetime.now(ist).strftime('%d-%b %H:%M')
        
        print(f"Option chain saved to: {output_file}")
        print(f"Timestamp: {current_time} IST")
        print(f"Underlying: {data['records']['underlyingValue']}")
        print(f"Expiry: {expiry}")
        print(f"Rows: {len(df)}")
        
    else:
        print("Failed to fetch option chain data")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/option-chain'
}

def get_future_price(symbol="NIFTY"):
    try:
        if "NIFTY" in symbol.upper():
            url = "https://scanner.tradingview.com/symbol?symbol=NSEIX:NIFTY1!&fields=close&no_404=true"
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
            return float(data.get('close', 0))
        return 0
    except Exception as e:
        print(f"Warning: Could not fetch future price: {e}")
        return 0

def get_next_tuesday():
    """Get the next Tuesday expiry date, skipping holidays"""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    today = now.date()
    
    # Start from today and find next Tuesday
    days_ahead = 1 - today.weekday()  # Tuesday is weekday 1
    if days_ahead < 0 or (days_ahead == 0 and now.hour >= 16):
        days_ahead += 7
    
    next_tuesday_date = today + timedelta(days=days_ahead)
    
    # Convert to string format for API
    return next_tuesday_date.strftime('%d-%b-%Y').upper()

def round_to_nearest_100(price):
    return round(price / 100) * 100

def get_filtered_strike_prices(data, strike_range=10):
    underlying_value = data['records']['underlyingValue']
    rounded_strike = round_to_nearest_100(underlying_value)
    
    all_strikes = sorted([item['strikePrice'] for item in data['records']['data'] if item['strikePrice'] % 100 == 0])
    
    target_index = all_strikes.index(rounded_strike) if rounded_strike in all_strikes else \
                   min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - rounded_strike))
    
    start_index = max(0, target_index - strike_range)
    end_index = min(len(all_strikes), target_index + strike_range + 1)
    
    return all_strikes[start_index:end_index], underlying_value, rounded_strike, target_index - start_index

def get_option_chain(symbol="NIFTY", expiry=None):
    if expiry is None:
        expiry = get_next_tuesday()
    
    url = f"https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol={symbol}&expiry={expiry}"
    
    session = requests.Session()
    session.headers.update(headers)
    session.get("https://www.nseindia.com")
    
    response = session.get(url)
    data = response.json()
    
    return data, expiry

def find_atm_strike_and_prices(df, reference_price):
    """
    Find ATM strike based on reference price (could be spot or future)
    """
    valid_rows = []
    for _, row in df.iterrows():
        if isinstance(row['STRIKE'], (int, float)):
            valid_rows.append(row)
    
    if not valid_rows:
        return None, 0, 0
    
    # Use reference_price (future_price in sensibull mode)
    atm_strike = min(valid_rows, key=lambda x: abs(x['STRIKE'] - reference_price))['STRIKE']
    
    atm_row = None
    for _, row in df.iterrows():
        if row['STRIKE'] == atm_strike:
            atm_row = row
            break
    
    if atm_row is None:
        return atm_strike, 0, 0
    
    atm_call_price = float(atm_row['CALL LTP']) if atm_row['CALL LTP'] not in ['', None] else 0
    atm_put_price = float(atm_row['PUT LTP']) if atm_row['PUT LTP'] not in ['', None] else 0
    
    return atm_strike, atm_call_price, atm_put_price

def should_use_call_iv(strike, reference_price, mode='sensibull'):
    """
    Determine whether to use Call IV or Put IV for a given strike
    For SENSIBULL mode: use reference_price (future price)
    """
    if mode == 'sensibull':
        # For sensibull: use reference price (future price) as the cutoff
        return strike >= reference_price
    else:
        # For other modes: use ATM strike (not implemented here)
        return strike >= reference_price

def calculate_iv_for_dataframe(df, spot_price, future_price, expiry_datetime):
    # Use FUTURE price for ATM selection in SENSIBULL mode
    atm_strike, atm_call_price, atm_put_price = find_atm_strike_and_prices(df, future_price)
    
    if atm_strike is None:
        return [''] * len(df)
    
    iv_values = []
    
    for _, row in df.iterrows():
        if not isinstance(row['STRIKE'], (int, float)):
            iv_values.append('')
            continue
            
        strike = float(row['STRIKE'])
        
        call_price = float(row['CALL LTP']) if row['CALL LTP'] not in ['', None] else 0
        put_price = float(row['PUT LTP']) if row['PUT LTP'] not in ['', None] else 0
        
        if call_price <= 0 and put_price <= 0:
            iv_values.append('')
            continue
        
        # Check for intrinsic value violations
        call_intrinsic = max(0, future_price - strike)
        put_intrinsic = max(0, strike - future_price)
        
        # If price is below intrinsic, use minimum price that makes sense
        calc_call_price = max(call_price, call_intrinsic + 0.01, 0.01)
        calc_put_price = max(put_price, put_intrinsic + 0.01, 0.01)
        
        try:
            calculator = CalcIvGreeks(
                SpotPrice=spot_price,  # Keep spot for NSE mode compatibility
                FuturePrice=future_price,
                AtmStrike=atm_strike,
                AtmStrikeCallPrice=atm_call_price if atm_call_price > 0 else 1.0,
                AtmStrikePutPrice=atm_put_price if atm_put_price > 0 else 1.0,
                ExpiryDateTime=expiry_datetime,
                StrikePrice=strike,
                StrikeCallPrice=calc_call_price,
                StrikePutPrice=calc_put_price,
                tryMatchWith=TryMatchWith.SENSIBULL
            )
            
            # Key change: Use future price comparison for SENSIBULL mode
            use_call = should_use_call_iv(strike, future_price, mode='sensibull')
            
            if use_call:
                iv = calculator.CallImplVol() * 100
            else:
                iv = calculator.PutImplVol() * 100
            
            if iv > 0:
                iv_values.append(round(iv, 2))
            else:
                iv_values.append('')
                
        except Exception:
            iv_values.append('')
    
    return iv_values

def create_option_chain_dataframe(data, expiry_date):
    filtered_strikes, underlying_value, rounded_strike, _ = get_filtered_strike_prices(data)
    
    strike_map = {item['strikePrice']: item for item in data['records']['data'] if item['strikePrice'] % 100 == 0}
    
    option_data = []
    inserted_underlying = False
    
    for strike in filtered_strikes:
        if strike not in strike_map:
            continue
        
        if strike > underlying_value and not inserted_underlying:
            option_data.append({
                'CALL OI': '', 'CALL OI CHNG': '', 'CALL VOLUME': '', 
                'CALL CHNG': '', 'CALL LTP': '', 'STRIKE': f"{underlying_value}",
                'PUT LTP': 'Expiry: ' + expiry_date, 'PUT CHNG': '', 
                'PUT VOLUME': '', 'PUT OI CHNG': '', 'PUT OI': ''
            })
            inserted_underlying = True
        
        item = strike_map[strike]
        ce_data = item.get('CE', {})
        pe_data = item.get('PE', {})
        
        option_data.append({
            'CALL OI': ce_data.get('openInterest', 0),
            'CALL OI CHNG': ce_data.get('changeinOpenInterest', 0),
            'CALL VOLUME': ce_data.get('totalTradedVolume', 0),
            'CALL CHNG': ce_data.get('change', 0),
            'CALL LTP': ce_data.get('lastPrice', 0),
            'STRIKE': strike,
            'PUT LTP': pe_data.get('lastPrice', 0),
            'PUT CHNG': pe_data.get('change', 0),
            'PUT VOLUME': pe_data.get('totalTradedVolume', 0),
            'PUT OI CHNG': pe_data.get('changeinOpenInterest', 0),
            'PUT OI': pe_data.get('openInterest', 0)
        })
    
    if not inserted_underlying:
        option_data.append({
            'CALL OI': '', 'CALL OI CHNG': '', 'CALL VOLUME': '', 
            'CALL CHNG': '', 'CALL LTP': '', 'STRIKE': f"{underlying_value}",
            'PUT LTP': 'Expiry: ' + expiry_date, 'PUT CHNG': '', 
            'PUT VOLUME': '', 'PUT OI CHNG': '', 'PUT OI': ''
        })
    
    df = pd.DataFrame(option_data)
    
    spot_price = underlying_value
    future_price = get_future_price()
    
    expiry_datetime = datetime.strptime(expiry_date, '%d-%b-%Y')
    expiry_datetime = expiry_datetime.replace(hour=15, minute=30, second=0)
    expiry_datetime = pytz.timezone('Asia/Kolkata').localize(expiry_datetime)
    
    iv_column = calculate_iv_for_dataframe(df, spot_price, future_price, expiry_datetime)
    
    df['IV'] = iv_column
    
    columns_order = ['CALL OI', 'CALL OI CHNG', 'CALL VOLUME', 'CALL CHNG', 'CALL LTP',
                     'STRIKE', 'IV', 
                     'PUT LTP', 'PUT CHNG', 'PUT VOLUME', 'PUT OI CHNG', 'PUT OI']
    df = df[columns_order]
    
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%d-%b %H:%M')
    
    timestamp_row = pd.DataFrame([{
        'CALL OI': '', 'CALL OI CHNG': '', 'CALL VOLUME': '', 
        'CALL CHNG': '', 'CALL LTP': '', 'STRIKE': '',
        'IV': '', 
        'PUT LTP': '', 'PUT CHNG': '', 'PUT VOLUME': '',
        'PUT OI CHNG': 'Update Time', 'PUT OI': current_time
    }])
    
    df = pd.concat([df, timestamp_row], ignore_index=True)
    
    return df

if __name__ == "__main__":
    main()
