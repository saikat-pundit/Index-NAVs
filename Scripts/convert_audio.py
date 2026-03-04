import os
import sys
import yt_dlp
import base64
from pathlib import Path

def setup_cookies():
    """Setup cookies from environment variable or file"""
    # Check if cookies base64 is in environment
    cookies_base64 = os.environ.get('YOUTUBE_COOKIES_BASE64')
    
    if cookies_base64:
        try:
            # Decode base64 to cookies.txt
            cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
            with open('cookies.txt', 'w') as f:
                f.write(cookies_content)
            print("✅ Cookies restored from GitHub Secret")
            return True
        except Exception as e:
            print(f"⚠️ Error decoding cookies: {e}")
    
    # Check if cookies.txt exists locally
    if os.path.exists('cookies.txt'):
        print("✅ Using local cookies.txt file")
        return True
    
    print("⚠️ No cookies found. Authentication may fail.")
    return False

def download_and_convert(youtube_url):
    """Download YouTube video and convert to 32kbps M4A"""
    
    # Setup cookies
    has_cookies = setup_cookies()
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '32',
        }],
        'outtmpl': 'audio_output/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        # Add delays to avoid rate limiting
        'sleep_interval': 5,
        'max_sleep_interval': 10,
        'sleep_interval_requests': 1,
    }
    
    # Add cookies if available
    if has_cookies:
        ydl_opts['cookiefile'] = 'cookies.txt'
        # Count cookies for verification
        try:
            with open('cookies.txt', 'r') as f:
                cookie_count = sum(1 for line in f 
                                 if line.strip() and not line.startswith('#'))
            print(f"📊 Loaded {cookie_count} cookies for authentication")
        except:
            pass
    
    try:
        # Create output directory
        Path("audio_output").mkdir(parents=True, exist_ok=True)
        
        # Download and convert
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n🔄 Processing URL: {youtube_url}")
            ydl.download([youtube_url])
        
        print("\n✅ Audio conversion completed successfully!")
        
        # List all files
        print("\n📁 Files created:")
        for file in Path("audio_output").iterdir():
            file_size = file.stat().st_size / (1024 * 1024)  # Convert to MB
            print(f"  - {file.name} ({file_size:.2f} MB)")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        
        if "Sign in to confirm" in str(e):
            print("\n🔑 Authentication failed. Possible reasons:")
            print("   1. Cookies have expired - need to refresh")
            print("   2. YouTube is blocking the request")
            print("   3. Need to add more delay between requests")
        
        sys.exit(1)
    finally:
        # Clean up temporary cookies file if created from secret
        if os.environ.get('YOUTUBE_COOKIES_BASE64') and os.path.exists('cookies.txt'):
            os.remove('cookies.txt')
            print("🧹 Cleaned up temporary cookies file")

def main():
    # Get URL from command line
    if len(sys.argv) > 1:
        youtube_url = sys.argv[1]
    else:
        youtube_url = input("Enter YouTube URL: ").strip()
    
    if not youtube_url:
        print("No URL provided. Exiting...")
        sys.exit(1)
    
    download_and_convert(youtube_url)

if __name__ == "__main__":
    main()
