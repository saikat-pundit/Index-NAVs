from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

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
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        # Navigate to the website
        driver.get("https://web.sensibull.com/stock-market-calendar/economic-calendar")
        
        # Wait for page to load and cookies to be set
        time.sleep(5)
        
        # Get all cookies
        cookies = driver.get_cookies()
        
        # Format cookies as a string for the header
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        
        # Add the prefix
        final_cookie = f"sb_rudder_utm={{}}; {cookie_string}"
        
        # Print ONLY the final cookie string (this will appear in GitHub Actions logs)
        print(final_cookie)
        
        return final_cookie
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_sensibull_cookies()
