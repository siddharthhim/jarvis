import logging
import os
import asyncio
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, room_io, cli
from livekit.plugins import google, silero

# ── Tool imports ───────────────────────────────────────────────────────────
# NOTE: modules prefixed with (*) are NOT in the repo — create them or remove.
# Stubs are provided so the agent at least starts without crashing.

# Safely import optional/missing modules so startup never crashes
def _safe_import(module: str, *names):
    """Returns a dict of {name: obj} for successfully imported names, else empty."""
    try:
        mod = __import__(module, fromlist=names)
        return {n: getattr(mod, n) for n in names if hasattr(mod, n)}
    except ImportError as e:
        logging.getLogger(__name__).warning(f"Optional module '{module}' not found: {e}")
        return {}

# Core tools that DO exist in the repo
from jarvis_memory import store_memory, recall_memory
from jarvis_doc_indexer import index_documents, search_documents
from jarvis_browser_agent import web_automation_task
from jarvis_synthesizer import synthesize_new_tool
from jarvis_screenshot import tool_take_screenshot
from jarvis_clipboard import read_clipboard, write_clipboard
from jarvis_system_info import get_system_info
from keyboard_mouse_CTRL import (
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
)
from jarvis_screenshare import capture_screen_tool, smart_window_ctrl

# Tools that may or may not exist locally — safe-imported
_google_search = _safe_import("Jarvis_google_search", "web_search", "get_current_datetime")
_weather       = _safe_import("jarvis_weather", "get_weather")
_email         = _safe_import("jarvis_email", "send_email")
_whatsapp      = _safe_import("jarvis_whatsapp", "send_whatsapp_message")
_youtube       = _safe_import("jarvis_youtube", "play_youtube")
_toolbox       = _safe_import("jarvis_toolbox", "download_youtube_video")
_window_ctrl   = _safe_import("Jarvis_window_CTRL", "open", "close", "folder_file", "create_folder_tool")
_file_opener   = _safe_import("Jarvis_file_opner", "Play_file")
_pdf_creator   = _safe_import("jarvis_pdf_creator", "create_pdf")
_ambient       = _safe_import("jarvis_ambient", "save_ambient_plan")
_forager       = _safe_import("jarvis_forager", "forage_knowledge")
_sentient      = _safe_import("sentient", "global_person_recon")
_dork          = _safe_import("google_dork", "run_passive_dork", "check_account_breach")
_prompts       = _safe_import("Jarvis_prompts", "instructions_prompt", "Reply_prompts")

load_dotenv()

logger = logging.getLogger("jarvis_agent")
logger.setLevel(logging.INFO)

# ── Build tool list from whatever actually loaded ──────────────────────────
_OPTIONAL_TOOLS = [
    _google_search.get("web_search"),
    _google_search.get("get_current_datetime"),
    _weather.get("get_weather"),
    _email.get("send_email"),
    _whatsapp.get("send_whatsapp_message"),
    _youtube.get("play_youtube"),
    _toolbox.get("download_youtube_video"),
    _window_ctrl.get("open"),
    _window_ctrl.get("close"),
    _window_ctrl.get("folder_file"),
    _window_ctrl.get("create_folder_tool"),
    _file_opener.get("Play_file"),
    _pdf_creator.get("create_pdf"),
    _ambient.get("save_ambient_plan"),
    _forager.get("forage_knowledge"),
    _sentient.get("global_person_recon"),
    _dork.get("run_passive_dork"),
    _dork.get("check_account_breach"),
]

JARVIS_TOOLS = [
    # Always-present tools
    store_memory, recall_memory,
    index_documents, search_documents,
    web_automation_task, synthesize_new_tool,
    tool_take_screenshot, capture_screen_tool, smart_window_ctrl,
    get_system_info, read_clipboard, write_clipboard,
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
    # Optional tools — filtered to only loaded ones
    *[t for t in _OPTIONAL_TOOLS if t is not None],
]

logger.info(f"Jarvis loaded {len(JARVIS_TOOLS)} tools.")

# ── System prompt ──────────────────────────────────────────────────────────
_instructions_prompt = _prompts.get("instructions_prompt", "")
_reply_prompts       = _prompts.get("Reply_prompts", "")

JARVIS_INSTRUCTIONS = f"""
You are JARVIS — an advanced autonomous AI assistant.
You have tools for voice, memory, desktop control, browser automation,
document intelligence, research, communication, and system monitoring.
Be concise in voice responses. Use Hinglish naturally when responding.
Think step-by-step before using tools. Always confirm destructive actions.
{_instructions_prompt}
{_reply_prompts}
""".strip()


# ── Agent class (new v1.5 pattern) ─────────────────────────────────────────
class JarvisAgent(Agent):
    """Main Jarvis voice agent with all tools pre-loaded."""

    def __init__(self) -> None:
        super().__init__(
            instructions=JARVIS_INSTRUCTIONS,
            tools=JARVIS_TOOLS,
        )


# ── Server setup (new v1.5 pattern) ───────────────────────────────────────
server = AgentServer()


@server.rtc_session(agent_name="jarvis")
async def jarvis_session(ctx: agents.JobContext):
    logger.info(f"✨ JARVIS online in room: {ctx.room.name}")

    await ctx.connect()

    session = AgentSession(
        stt=google.STT(model="chirp"),           # Google Cloud STT (Chirp) — needs GOOGLE_APPLICATION_CREDENTIALS
        llm=google.LLM(model="gemini-2.5-flash"), # Stable non-exp model
        tts=google.TTS(
            gender="male",
            voice_name="en-IN-Standard-B",        # Indian English voice — fits Hinglish persona
        ),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=JarvisAgent(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # Noise cancellation — uncomment after: pip install livekit-plugins-ai-coustics
                # noise_cancellation=ai_coustics.audio_enhancement(),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user. Say 'System online. All modules integrated and ready, Sir.'"
    )


if __name__ == "__main__":
    cli.run_app(server)
