import os
import sys
import platform
import asyncio
import logging
import subprocess
from datetime import datetime
from livekit.agents import function_tool

logger = logging.getLogger(__name__)

_PLANS_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Jarvis Plans")
os.makedirs(_PLANS_DIR, exist_ok=True)


def _open_file_cross_platform(filepath: str):
    """Opens a file in the default text editor for the current OS."""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen(["notepad.exe", filepath])
        elif system == "Darwin":
            subprocess.Popen(["open", "-t", filepath])
        else:
            # Linux — try common editors in order
            for editor in ["xdg-open", "gedit", "nano", "vim"]:
                try:
                    subprocess.Popen([editor, filepath])
                    return
                except FileNotFoundError:
                    continue
            logger.warning("No suitable text editor found to open the plan file.")
    except Exception as e:
        logger.warning(f"Could not open file in editor: {e}")


@function_tool
async def save_ambient_plan(topic: str, content: str) -> str:
    """
    Saves a detailed plan into the 'Jarvis Plans' folder on the Desktop
    and opens it in the system's default text editor.

    Args:
        topic (str): The subject or title of the plan.
        content (str): The full plan content to save.
    """
    try:
        timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
        safe_topic = "".join(
            c for c in topic[:40] if c.isalnum() or c in " _-"
        ).strip()
        filename = f"{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(_PLANS_DIR, filename)

        file_header = (
            f"JARVIS AMBIENT ASSIST\n{'=' * 50}\n"
            f"Generated : {timestamp}\nTopic     : {topic}\n{'=' * 50}\n\n"
        )

        def _write_and_open():
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_header + content)
            _open_file_cross_platform(filepath)

        await asyncio.to_thread(_write_and_open)
        logger.info(f"Ambient plan saved: {filepath}")
        return f"✅ Plan for '{topic}' saved and opened Sir। Location: {filepath}"
    except Exception as e:
        logger.exception(f"Ambient save error: {e}")
        return f"❌ Plan save नहीं हो पाई Sir: {e}"
