import os
import sys
import yt_dlp
from pathlib import Path

def create_cookies_file_from_env():
    """Create cookies.txt from environment variable"""
    cookie_value = os.environ.get('YOUTUBE_COOKIE')
    
    if cookie_value:
        print("✅ Found YouTube cookie in environment")
        
        # Create cookies.txt in Netscape format
        with open('cookies.txt', 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            # Format: domain\tTRUE\tpath\tsecure\texpiry\tname\tvalue
            # Using a far future expiry (2030-01-01)
            f.write(f".youtube.com\tTRUE\t/\tTRUE\t1893456000\t__Secure-1PAPISID\t{cookie_value}\n")
            
            # Also add related cookies that often work together
            f.write(f".youtube.com\tTRUE\t/\tTRUE\t1893456000\t__Secure-1PSID\t\n")
            f.write(f".youtube.com\tTRUE\t/\tTRUE\t1893456000\t__Secure-1PSIDCC\t\n")
        
        print("✅ cookies.txt created from environment variable")
        return True
    
    # Check if cookies.txt already exists
    if os.path.exists('cookies.txt'):
        print("✅ Using existing cookies.txt")
        return True
    
    print("⚠️ No cookies found")
    return False

def download_and_convert(youtube_url):
    """Download YouTube video and convert to 32kbps M4A"""
    
    # Create cookies file if env var exists
    has_cookies = create_cookies_file_from_env()
    
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
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    
    # Add cookies if available
    if has_cookies:
        ydl_opts['cookiefile'] = 'cookies.txt'
        print("🔑 Using cookies for authentication")
    
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
            print(f"  - {file.name}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
    finally:
        # Clean up cookies file (optional)
        if os.path.exists('cookies.txt') and os.environ.get('YOUTUBE_COOKIE'):
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
