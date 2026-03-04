import os
import sys
import yt_dlp
from pathlib import Path

def download_and_convert(youtube_url):
    """Download YouTube video and convert to 32kbps M4A"""
    
    # Configure yt-dlp options for audio extraction
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
    }
    
    try:
        # Create output directory if it doesn't exist
        Path("audio_output").mkdir(parents=True, exist_ok=True)
        
        # Download and convert
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Processing URL: {youtube_url}")
            ydl.download([youtube_url])
        
        print("\n✅ Audio conversion completed successfully!")
        print("📁 Check the 'audio_output' directory for your file.")
        
        # List all files in the output directory
        print("\nFiles created:")
        for file in Path("audio_output").iterdir():
            print(f"  - {file.name}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

def main():
    # Get URL from command line argument or prompt
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
