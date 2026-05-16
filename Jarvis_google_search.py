import os
import logging
import httpx
from datetime import datetime  # Add this import
from typing import Annotated
from livekit.agents import function_tool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("jarvis")

@function_tool
async def web_search(
    query: Annotated[str, "The search query to look up"]
) -> str:
    """Searches the web for real-time information and news."""
    
    # Getting the key from .env
    api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key or api_key == "YOUR_TAVILY_API_KEY":
        logger.error("Sir, the Tavily API key is missing from the .env file.")
        return "Sir, I cannot access the web because the API key is not configured in our environment."

    logger.info(f"Sir, scanning the global network for: {query}")
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 3
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=15.0)
            
            if response.status_code == 401:
                return "Sir, the search API returned an Unauthorized error. Please check if the API key is valid."
            
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return "I searched the web, sir, but no relevant results were found."
            
            # Formatting results for a natural voice response
            formatted = []
            for r in results:
                formatted.append(f"Source: {r['title']}\nSnippet: {r['content']}")
            
            return "\n\n".join(formatted)
            
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Sir, I encountered an error while searching: {str(e)}"


@function_tool
async def get_current_datetime() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%d %B %Y, %I:%M %p")