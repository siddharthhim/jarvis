import logging
import os
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, room_io, cli
from livekit.plugins import google, silero

# Re-use the same safe tool loading from agent.py
# Import everything that's available
def _safe_import(module: str, *names):
    try:
        mod = __import__(module, fromlist=names)
        return {n: getattr(mod, n) for n in names if hasattr(mod, n)}
    except ImportError as e:
        logging.getLogger(__name__).warning(f"Optional module '{module}' not found: {e}")
        return {}

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

_optional = {}
for mod, names in [
    ("Jarvis_google_search", ("web_search", "get_current_datetime")),
    ("jarvis_weather",       ("get_weather",)),
    ("jarvis_email",         ("send_email",)),
    ("jarvis_whatsapp",      ("send_whatsapp_message",)),
    ("jarvis_youtube",       ("play_youtube",)),
    ("jarvis_toolbox",       ("download_youtube_video",)),
    ("Jarvis_window_CTRL",   ("open", "close", "folder_file", "create_folder_tool")),
    ("Jarvis_file_opner",    ("Play_file",)),
    ("jarvis_pdf_creator",   ("create_pdf",)),
    ("jarvis_ambient",       ("save_ambient_plan",)),
    ("jarvis_forager",       ("forage_knowledge",)),
    ("sentient",             ("global_person_recon",)),
    ("google_dork",          ("run_passive_dork", "check_account_breach")),
]:
    _optional.update(_safe_import(mod, *names))

_prompts = _safe_import("Jarvis_prompts", "instructions_prompt", "Reply_prompts")

load_dotenv()
logger = logging.getLogger("jarvis_multimodal")
logger.setLevel(logging.INFO)

JARVIS_TOOLS = [
    store_memory, recall_memory,
    index_documents, search_documents,
    web_automation_task, synthesize_new_tool,
    tool_take_screenshot, capture_screen_tool, smart_window_ctrl,
    get_system_info, read_clipboard, write_clipboard,
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
    *[t for t in _optional.values() if t is not None],
]

logger.info(f"Multimodal JARVIS loaded {len(JARVIS_TOOLS)} tools.")

_instructions = _prompts.get("instructions_prompt", "")
_replies      = _prompts.get("Reply_prompts", "")

JARVIS_INSTRUCTIONS = f"""
You are JARVIS — an advanced multimodal autonomous AI assistant.
You can see, hear, and act. You have full desktop, browser, memory, and research capabilities.
Be concise in voice responses. Use Hinglish naturally when responding.
{_instructions}
{_replies}
""".strip()


class JarvisMultimodalAgent(Agent):
    """Jarvis agent using Gemini Live API for native speech-to-speech."""

    def __init__(self) -> None:
        super().__init__(
            instructions=JARVIS_INSTRUCTIONS,
            tools=JARVIS_TOOLS,
        )


server = AgentServer()


@server.rtc_session(agent_name="jarvis-multimodal")
async def jarvis_multimodal_session(ctx: agents.JobContext):
    logger.info(f"🚀 Multimodal JARVIS online in room: {ctx.room.name}")

    await ctx.connect()

    session = AgentSession(
        # Gemini Live API — native speech-to-speech, no STT/TTS needed separately
        llm=google.realtime.RealtimeModel(
            model="gemini-2.5-flash",   # stable model — NOT the deprecated -exp variant
            voice="Charon",
        ),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=JarvisMultimodalAgent(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # Noise cancellation — uncomment after: pip install livekit-plugins-ai-coustics
                # noise_cancellation=ai_coustics.audio_enhancement(),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user. Say 'Multimodal systems online. All modules integrated and ready, Sir.'"
    )


if __name__ == "__main__":
    cli.run_app(server)
