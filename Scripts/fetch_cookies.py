from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os

def fetch_sensibull_cookies():
    """Fetch cookies from sensibull.com without login"""
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User agent to appear as a real browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print("Starting Chrome browser...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        # Navigate to the website
        print("Navigating to sensibull.com...")
        driver.get("https://web.sensibull.com/stock-market-calendar/economic-calendar")
        
        # Wait for page to load and cookies to be set
        time.sleep(5)
        
        # Get all cookies
        cookies = driver.get_cookies()
        
        print(f"\n=== Found {len(cookies)} cookies ===\n")
        
        # Format cookies as a string for the header
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        
        # Print cookie string (this will appear in GitHub Actions logs)
        print("COOKIE_STRING:")
        print(cookie_string)
        print("\n" + "="*50 + "\n")
        
        # Also print individual cookies for debugging
        print("Individual Cookies:")
        for cookie in cookies:
            print(f"  {cookie['name']}: {cookie['value'][:50]}...")
        
        # Save to file for later use
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        
        # Save the cookie string to a file
        with open('cookie_string.txt', 'w') as f:
            f.write(cookie_string)
        
        print("\nCookies saved to cookies.json and cookie_string.txt")
        
        return cookie_string
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_sensibull_cookies()
