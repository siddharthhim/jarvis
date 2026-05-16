import os
import asyncio
import logging
import pyautogui
from livekit.agents import function_tool

logger = logging.getLogger(__name__)

@function_tool
async def send_whatsapp_message(contact_name: str, message: str) -> str:
    """
    Sends a WhatsApp message using the WhatsApp Desktop app.
    
    Args:
        contact_name (str): Person's name (e.g., 'Mom', 'Dad') or phone number.
        message (str): The content of the message.
    """
    try:
        # 1. Launch/Focus WhatsApp Desktop
        whatsapp_app_path = r"shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
        os.startfile(whatsapp_app_path)
        
        # Wait for app to open and gain focus
        await asyncio.sleep(4)
        
        # 2. Search for the contact (Ctrl + F is often used for search in WhatsApp Desktop)
        # Some versions use Ctrl+N or just clicking the search bar. Ctrl+F is standard.
        pyautogui.hotkey('ctrl', 'f')
        await asyncio.sleep(0.5)
        
        # 3. Type the contact name or number
        pyautogui.write(contact_name, interval=0.05)
        await asyncio.sleep(1.0)
        
        # 4. Press enter to select the first contact in search results
        pyautogui.press('enter')
        await asyncio.sleep(0.5)
        
        # 5. Type the message
        pyautogui.write(message, interval=0.05)
        await asyncio.sleep(0.5)
        
        # 6. Press enter to send
        pyautogui.press('enter')
        
        logger.info(f"WhatsApp message sent to '{contact_name}' via Desktop App")
        return f"Sir, Desktop App se '{contact_name}' ko message भेज दिया है।"

    except Exception as e:
        logger.error(f"WhatsApp Desktop automation failed: {e}")
        return f"Sir, Desktop App open करके message भेजने में problem आई: {e}"
