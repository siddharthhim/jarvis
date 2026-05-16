import logging
from livekit.agents import function_tool
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

@function_tool
async def run_passive_dork(query: str) -> str:
    """
    Perform passive OSINT and Google/DDG Dorking to find leaked files, 
    admin panels, or sensitive indexed data.
    """
    logger.info(f"Jarvis executing Dork scan: {query}")

    try:
        # DDGS supports operators like site:, filetype:, intitle:, inurl:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
    except Exception as e:
        logger.error(f"Dorking failed: {e}")
        return "Passive scan failed."

    if not results:
        return "Scan complete. No public leaks or matching files found in the index."

    output = "Sentinel Scan Results:\n"
    for i, r in enumerate(results, 1):
        output += f"{i}. {r.get('title')} - {r.get('href')}\nSnippet: {r.get('body')}\n\n"

    return output.strip()

@function_tool
async def check_account_breach(email: str) -> str:
    """
    Checks if an email or account has been part of a known data breach (Passive OSINT).
    """
    # For a real build, you'd hit an API like HaveIBeenPwned here.
    # For now, we can use DDGS to see if the email appears in public leak lists/pastes.
    query = f'"{email}" leak OR breach OR pastebin'
    logger.info(f"Checking breach status for: {email}")

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return f"No immediate public leaks found for {email}."
            
            return f"Caution: I found mentions of {email} in public search results related to leaks. Please review."
    except Exception as e:
        return "Breach check failed."