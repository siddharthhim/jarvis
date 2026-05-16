import os
import asyncio
import logging
import pyautogui
import pygetwindow as gw
from PIL import Image
from livekit.agents import function_tool
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

# Setup Logger for Aurex Systems
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JarvisVision")

# ---------------------------------------------------------
# 1. SafeController Class (Security & State)
# ---------------------------------------------------------
class SafeController:
    def __init__(self):
        self.active = False
        self.keyboard = KeyboardController()
        self.mouse = MouseController()

    def activate(self, token="my_secret_token"):
        # Auto-activation logic for tool execution
        self.active = True
        
    def deactivate(self):
        self.active = False

    def is_active(self):
        return self.active

# Global instance so all tools can access it
controller = SafeController()

# ---------------------------------------------------------
# 2. Vision & Screenshare Capability
# ---------------------------------------------------------

@function_tool
async def capture_screen_tool(mode: str = "active") -> str:
    """Captures the screen so Jarvis can see the current state."""
    controller.activate()
    try:
        # Give a tiny delay for UI stability
        await asyncio.sleep(0.5)
        
        if mode == "active":
            win = gw.getActiveWindow()
            if win and win.title:
                # Region: (left, top, width, height)
                screenshot = pyautogui.screenshot(region=(win.left, win.top, win.width, win.height))
                label = f"Active Window: {win.title}"
            else:
                screenshot = pyautogui.screenshot()
                label = "Full Desktop (No active window detected)"
        else:
            screenshot = pyautogui.screenshot()
            label = "Full Desktop"

        # Optimize for AI Vision: JPEG 85% is faster to upload to the LLM
        screenshot = screenshot.convert("RGB")
        screenshot.save("jarvis_vision.jpg", "JPEG", quality=85)
        
        logger.info(f"📸 Visual Context Saved: {label}")
        return f"SUCCESS|{label}" 
    except Exception as e:
        logger.error(f"❌ Vision Error: {e}")
        return f"ERROR|{str(e)}"
    finally:
        controller.deactivate()

# ---------------------------------------------------------
# 3. Window & Control Capability
# ---------------------------------------------------------

@function_tool
async def smart_window_ctrl(action: str, target_app: str = "") -> str:
    """Controls windows: 'switch' (Alt+Tab) or 'focus' (Bring app to front)."""
    controller.activate()
    try:
        if action == "switch":
            pyautogui.hotkey('alt', 'tab')
            return "Switched to the next window, sir."
            
        elif action == "focus" and target_app:
            # Manual loop to find the window (fixes the missing import error)
            target_app = target_app.lower()
            for window in gw.getAllWindows():
                if target_app in window.title.lower():
                    window.activate()
                    if window.isMinimized:
                        window.restore()
                    return f"Successfully focused on {window.title}."
            return f"Sir, I couldn't find a window matching '{target_app}'."
            
        return "Command not recognized for window control."
    finally:
        controller.deactivate()