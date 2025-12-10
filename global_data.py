import yfinance as yf
import pandas as pd
from datetime import datetime
import time

TICKERS = {
    "Dow Jones": "^DJI",
    "S&P 500": "^GSPC", 
    "NASDAQ 100": "^NDX",
    "VIX": "^VIX",
    "US 10-Year Yield": "^TNX",
    "Nikkei 225": "^N225",
    "Euro Stoxx 50": "^STOXX50E",
    "FTSE 100": "^FTSE",
    "Gold ETF": "GLD",
    "Silver ETF": "SLV"
}

def safe_history(ticker_obj, period):
    for attempt in range(3):
        try:
            return ticker_obj.history(period=period, backend="scraper")
        except Exception as e:
            print(f"  Retry {attempt+1}/3 ... ({e})")
            time.sleep(2)
    return None

def fetch_global_data():
    print("Fetching global market data...")
    print("="*60)
    
    records = []

    for name, ticker in TICKERS.items():
        print(f"Fetching {name} ({ticker})...")

        ticker_obj = yf.Ticker(ticker)

        hist = safe_history(ticker_obj, "1mo")
        
        if hist is None or hist.empty or len(hist) < 2:
            print(f"  ⚠️  No data for {name}")
            continue

        latest = hist.iloc[-1]
        previous = hist.iloc[-2]

        last_price = latest["Close"]
        prev_close = previous["Close"]

        change = last_price - prev_close
        percent_change = (change / prev_close * 100) if prev_close else 0

        year_data = safe_history(ticker_obj, "1y")
        year_high = year_data["High"].max() if year_data is not None else last_price
        year_low  = year_data["Low"].min() if year_data is not None else last_price

        records.append({
            "Index Name": name,
            "Last": round(last_price, 2),
            "Change": round(change, 2),
            "% Change": f"{percent_change:+.2f}%",
            "Previous Close": round(prev_close, 2),
            "Year High": round(year_high, 2),
            "Year Low": round(year_low, 2),
        })

        print(f"  ✅ ${last_price:.2f} ({percent_change:+.2f}%)")

    if not records:
        print("‼️ Error: No data received!")
        return None

    df = pd.DataFrame(records)
    filename = "GLOBAL_DATA.csv"
    df.to_csv(filename, index=False)

    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    with open(filename, "a") as f:
        f.write(f"Update Time:,,,,,{timestamp}\n")

    print(f"\n✅ Data saved to {filename}")
    print(f"📊 {len(records)} instruments processed")
    print(f"🕐 Updated: {timestamp}")

    return df

if __name__ == "__main__":
    fetch_global_data()
