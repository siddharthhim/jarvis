import logging
import pyperclip
from livekit.agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def read_clipboard() -> str:
    """
    Reads and returns the current text content of the clipboard.

    Use when the user asks to read clipboard, paste, or 'what's in clipboard'.
    """
    try:
        content = pyperclip.paste()
        if not content:
            return "📋 Clipboard abhi खाली है, Sir।"
        logger.info("Clipboard read.")
        return f"📋 Clipboard में यह है:\n{content}"
    except Exception as e:
        logger.exception(f"Clipboard read error: {e}")
        return f"❌ Clipboard read नहीं हो पाया: {e}"


@function_tool
async def write_clipboard(text: str) -> str:
    """
    Writes the given text to the clipboard.

    Use when the user says 'copy this', 'put this in clipboard', or 'clipboard में डालो'.
    Args:
        text (str): The text to copy to clipboard.
    """
    try:
        pyperclip.copy(text)
        logger.info(f"Clipboard written: {text[:50]}")
        return f"✅ Done Sir, clipboard में copy हो गया।"
    except Exception as e:
        logger.exception(f"Clipboard write error: {e}")
        return f"❌ Clipboard write नहीं हो पाया: {e}"
