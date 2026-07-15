import requests
import json

def fetch_cookies_simple():
    """Fetch cookies using requests - simpler but may not get all cookies"""
    
    session = requests.Session()
    
    # Headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print("Fetching cookies with requests...")
    response = session.get(
        "https://web.sensibull.com/stock-market-calendar/economic-calendar",
        headers=headers
    )
    
    # Get cookies from the session
    cookies = session.cookies.get_dict()
    
    # Format as cookie string
    cookie_string = "; ".join([f"{key}={value}" for key, value in cookies.items()])
    
    print("\n=== COOKIES FOUND ===")
    print(cookie_string)
    print("\n" + "="*50)
    
    # Save to file
    with open('cookie_string.txt', 'w') as f:
        f.write(cookie_string)
    
    return cookie_string

if __name__ == "__main__":
    fetch_cookies_simple()
