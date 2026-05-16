import os
import logging
import yt_dlp
from livekit.agents import function_tool

logger = logging.getLogger(__name__)

# Folder where Jarvis downloads are saved
_DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Jarvis Downloads")
os.makedirs(_DOWNLOADS_DIR, exist_ok=True)

@function_tool
async def download_youtube_video(url: str) -> str:
    """
    Downloads a YouTube video to the 'Jarvis Downloads' folder on the Desktop.
    
    Args:
        url (str): The URL of the YouTube video to download.
    """
    try:
        ydl_opts = {
            'outtmpl': os.path.join(_DOWNLOADS_DIR, '%(title)s.%(ext)s'),
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        logger.info(f"YouTube video downloaded: {filename}")
        return f"Sir, video download ho gaya hai! Aap use Desktop par 'Jarvis Downloads' folder mein check kar sakte hain."
    except Exception as e:
        logger.error(f"YouTube download failed: {e}")
        return f"Sir, YouTube video download karne mein problem aayi: {e}"
