import pyautogui
import datetime
import os
import asyncio
from livekit.agents import function_tool

# ------------------------------
# Jarvis Tool: Screenshot
# ------------------------------

@function_tool
async def tool_take_screenshot() -> str:
    """
    Takes a full screenshot and saves it in the 'Screenshots' folder.
    Returns the filename where the screenshot was saved.
    """
    try:
        # Create folder if it doesn't exist
        if not os.path.exists("Screenshots"):
            os.makedirs("Screenshots")
        
        # Timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Screenshots/screenshot_{timestamp}.png"
        
        # Take screenshot and save
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        screenshot = await loop.run_in_executor(None, pyautogui.screenshot)
        await loop.run_in_executor(None, screenshot.save, filename)
        
        return f"Screenshot saved as {filename}"
        
    except Exception as e:
        return f"Failed to take screenshot: {str(e)}"