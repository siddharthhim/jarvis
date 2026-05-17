import logging
import os
import sys
import platform
import asyncio
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, VoicePipelineAgent
from livekit.plugins import google, silero

# ── Platform guard ────────────────────────────────────────────────────────────
# Several modules (Win32, PyAutoGUI, WhatsApp) only work on Windows.
# We warn loudly instead of crashing silently.
_IS_WINDOWS = platform.system() == "Windows"
if not _IS_WINDOWS:
    logging.warning(
        "⚠️  Jarvis: Non-Windows platform detected. "
        "Desktop control, keyboard/mouse, and WhatsApp tools will be unavailable."
    )

# ── Core tool imports (cross-platform) ───────────────────────────────────────
from Jarvis_google_search import web_search, get_current_datetime
from jarvis_memory import store_memory, recall_memory
from jarvis_browser_agent import web_automation_task
from jarvis_synthesizer import synthesize_new_tool, load_custom_tools
from jarvis_forager import forage_knowledge
from jarvis_doc_indexer import index_documents, search_documents
from jarvis_ambient import save_ambient_plan
from jarvis_system_info import get_system_info
from jarvis_clipboard import read_clipboard, write_clipboard
from jarvis_screenshot import tool_take_screenshot
from jarvis_screenshare import capture_screen_tool, smart_window_ctrl
from jarvis_email import send_email
from jarvis_youtube import play_youtube
from jarvis_toolbox import download_youtube_video
from google_dork import run_passive_dork, check_account_breach
from jarvis_prompts import instructions_prompt, reply_prompts

# ── Optional weather (requires jarvis_weather.py to exist) ───────────────────
try:
    from jarvis_weather import get_weather
    _HAS_WEATHER = True
except ImportError:
    _HAS_WEATHER = False
    logging.warning("jarvis_weather.py not found — weather tool disabled.")

# ── Windows-only tool imports ─────────────────────────────────────────────────
if _IS_WINDOWS:
    try:
        from Jarvis_window_CTRL import open as open_app, close as close_window, folder_file, create_folder_tool
        from jarvis_file_opener import Play_file   # fixed typo: opner → opener
        from jarvis_whatsapp import send_whatsapp_message
        from keyboard_mouse_CTRL import (
            move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
            press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool
        )
        _WINDOWS_TOOLS = [
            open_app, close_window, folder_file, create_folder_tool, Play_file,
            send_whatsapp_message,
            move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
            press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
        ]
    except ImportError as e:
        logging.warning(f"⚠️  Some Windows tools failed to load: {e}")
        _WINDOWS_TOOLS = []
else:
    _WINDOWS_TOOLS = []

# ── PDF creator (optional) ────────────────────────────────────────────────────
try:
    from jarvis_pdf_creator import create_pdf
    _PDF_TOOLS = [create_pdf]
except ImportError:
    _PDF_TOOLS = []
    logging.warning("jarvis_pdf_creator.py not found — PDF tool disabled.")

# ── Sentient person recon (optional) ─────────────────────────────────────────
try:
    from sentient import global_person_recon
    _SENTIENT_TOOLS = [global_person_recon]
except ImportError:
    _SENTIENT_TOOLS = []
    logging.warning("sentient module not found — person recon tool disabled.")

load_dotenv()
logger = logging.getLogger("jarvis_agent")
logger.setLevel(logging.INFO)

# ── Base tool registry ────────────────────────────────────────────────────────
JARVIS_TOOLS = [
    # Research / search
    run_passive_dork, check_account_breach,
    web_search, get_current_datetime,
    forage_knowledge,
    # Memory
    store_memory, recall_memory,
    # Comms
    send_email,
    play_youtube, download_youtube_video,
    # Desktop / screen (cross-platform)
    tool_take_screenshot, capture_screen_tool, smart_window_ctrl,
    get_system_info, read_clipboard, write_clipboard,
    # Documents
    index_documents, search_documents,
    save_ambient_plan,
    # Self-extension / browser
    web_automation_task, synthesize_new_tool,
]

# Append optional / platform-specific tools
if _HAS_WEATHER:
    JARVIS_TOOLS.append(get_weather)

JARVIS_TOOLS.extend(_WINDOWS_TOOLS)
JARVIS_TOOLS.extend(_PDF_TOOLS)
JARVIS_TOOLS.extend(_SENTIENT_TOOLS)


def prewarm(proc: agents.JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    logger.info(f"✨ JARVIS online in room: {ctx.room.name}")
    await ctx.connect()

    fnc_ctx = agents.llm.FunctionContext()

    # Register static tools
    for tool in JARVIS_TOOLS:
        fnc_ctx.add_tool(tool)

    # Hot-load any synthesized custom tools
    custom_tools = load_custom_tools()
    for tool in custom_tools:
        fnc_ctx.add_tool(tool)
    if custom_tools:
        logger.info(f"🔌 Loaded {len(custom_tools)} custom synthesized tool(s).")

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=google.STT(),
        llm=google.LLM(model="gemini-2.0-flash-exp"),
        tts=google.TTS(),
        fnc_ctx=fnc_ctx,
        chat_ctx=agents.llm.ChatContext().append(
            role="system",
            text=f"{instructions_prompt}\n\n{reply_prompts}",
        ),
    )

    agent.start(ctx.room)
    logger.info("🚀 JARVIS is now online.")
    await agent.say("System online. All modules integrated and ready.", allow_interruptions=True)

    # ── Fixed: is_connected() is a method, not a property ─────────────────────
    while ctx.room.is_connected():
        await asyncio.sleep(1)

    logger.info("Room disconnected — JARVIS shutting down.")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
