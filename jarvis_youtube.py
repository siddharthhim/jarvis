import webbrowser
import logging
from urllib.parse import quote_plus
from livekit.agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def play_youtube(query: str) -> str:
    """
    Searches and plays a YouTube video by opening it in the browser.

    Use when the user asks to play a song, video, or anything on YouTube.
    Args:
        query (str): Search term, song name, artist, or video title.
    """
    try:
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        webbrowser.open(search_url)
        logger.info(f"YouTube opened for query: {query}")
        return f"✅ YouTube पर '{query}' search कर दिया है, Sir। आप पसंदीदा video choose करें।"
    except Exception as e:
        logger.exception(f"YouTube open error: {e}")
        return f"❌ YouTube open करने में error आया: {e}"
