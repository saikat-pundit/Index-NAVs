import os
import sys
import yt_dlp
import base64
from pathlib import Path

def setup_cookies():
    """Setup cookies from environment variable"""
    cookies_base64 = os.environ.get('YOUTUBE_COOKIES_BASE64')
    
    if cookies_base64:
        try:
            cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
            if '# Netscape' in cookies_content or '# HTTP' in cookies_content:
                with open('cookies.txt', 'w') as f:
                    f.write(cookies_content)
                
                cookie_count = sum(1 for line in cookies_content.split('\n') 
                                 if line.strip() and not line.startswith('#'))
                print(f"✅ Cookies restored from secret ({cookie_count} cookies)")
                return True
        except Exception as e:
            print(f"⚠️ Error decoding cookies: {e}")
    
    if os.path.exists('cookies.txt'):
        print("✅ Using local cookies.txt file")
        return True
    
    print("⚠️ No cookies found")
    return False

def download_and_convert(youtube_url):
    """Download YouTube video and convert to 32kbps M4A"""
    
    has_cookies = setup_cookies()
    
    # Configure yt-dlp options - FIXED VERSION
    ydl_opts = {
        # Better format selection - try different audio formats
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '32',
        }],
        
        'outtmpl': 'audio_output/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        
        # User agent to avoid detection
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        
        # Use only clients that work well with cookies
        'extractor_args': {'youtube': {'player_client': ['web', 'web_creator']}},
        
        # Add delays to avoid rate limiting
        'sleep_interval': 5,
        'max_sleep_interval': 10,
        'sleep_interval_requests': 1,
        
        # Allow fallback to other formats
        'ignoreerrors': False,
        'nooverwrites': True,
        'continuedl': True,
        
        # Enable JavaScript runtime (Deno should be installed)
        'extractor_args': {'youtube': {'player_client': ['web', 'web_creator']}},
    }
    
    # Add cookies if available
    if has_cookies:
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        Path("audio_output").mkdir(parents=True, exist_ok=True)
        
        # First, list available formats for debugging
        with yt_dlp.YoutubeDL({'quiet': True, 'cookiefile': 'cookies.txt' if has_cookies else None}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            print("\n📋 Available formats:")
            formats_found = False
            for f in info.get('formats', []):
                if f.get('acodec') != 'none':  # Only show formats with audio
                    print(f"  - Format: {f.get('format_id')}, Quality: {f.get('quality')}, "
                          f"Codec: {f.get('acodec')}, Size: {f.get('filesize')}")
                    formats_found = True
            
            if not formats_found:
                print("  ⚠️ No audio formats found!")
        
        # Now download with the configured options
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n🔄 Processing URL: {youtube_url}")
            ydl.download([youtube_url])
        
        print("\n✅ Audio conversion completed successfully!")
        
        # List all files
        print("\n📁 Files created:")
        for file in Path("audio_output").iterdir():
            file_size = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name} ({file_size:.2f} MB)")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        
        if "Requested format is not available" in str(e):
            print("\n🔧 FIX: Trying alternative format...")
            # Try with different format selection
            ydl_opts['format'] = 'worstaudio/worst'
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
                print("\n✅ Success with alternative format!")
            except Exception as e2:
                print(f"\n❌ Still failing: {e2}")
        
        sys.exit(1)
    finally:
        if os.environ.get('GITHUB_ACTIONS') and os.path.exists('cookies.txt'):
            os.remove('cookies.txt')
            print("🧹 Cleaned up temporary cookies file")

def main():
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
