import os
import asyncio
import logging
import subprocess
from datetime import datetime
from livekit.agents import function_tool

logger = logging.getLogger(__name__)

_PLANS_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Jarvis Plans")
os.makedirs(_PLANS_DIR, exist_ok=True)

def _open_in_notepad(filepath: str):
    subprocess.Popen(["notepad.exe", filepath])

@function_tool
async def save_ambient_plan(topic: str, content: str) -> str:
    """
    Saves a detailed plan into the 'Jarvis Plans' folder and opens it in Notepad.
    """
    try:
        timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
        safe_topic = "".join(c for c in topic[:40] if c.isalnum() or c in " _-").strip()
        filename = f"{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(_PLANS_DIR, filename)

        file_header = (
            f"JARVIS AMBIENT ASSIST\n{'='*50}\n"
            f"Generated : {timestamp}\nTopic     : {topic}\n{'='*50}\n\n"
        )

        def _write_and_open():
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_header + content)
            _open_in_notepad(filepath)

        await asyncio.to_thread(_write_and_open)
        logger.info(f"Ambient plan saved: {filepath}")
        return f"Detailed plan for '{topic}' opened in Notepad."
    except Exception as e:
        logger.exception(f"Ambient save error: {e}")
        return f"Failed to save plan: {e}"