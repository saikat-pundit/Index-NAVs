import yfinance as yf
import pandas as pd
from datetime import datetime

# Tickers to fetch
tickers = {
    "SP500": "^GSPC",
    "DJI": "^DJI",
    "VIX": "^VIX",
    "AAPL": "AAPL",
    "META": "META"
}

def fetch_data():
    frames = []
    for name, ticker in tickers.items():
        print(f"Fetching {name} ({ticker})...")
        data = yf.download(ticker, period="1d", interval="1d")
        data.reset_index(inplace=True)
        data["Symbol"] = name
        frames.append(data)

    df = pd.concat(frames, ignore_index=True)

    # Output CSV file with timestamp
    filename = f"market_data_{datetime.now().strftime('%Y-%m-%d')}.csv"
    df.to_csv(filename, index=False)
    print(f"Saved data to {filename}")

if __name__ == "__main__":
    fetch_data()
