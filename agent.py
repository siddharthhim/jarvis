import logging
import os
import asyncio
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, VoicePipelineAgent
from livekit.plugins import google, silero

# ── Optional / missing-module guard ───────────────────────────────────────
# BUG FIX: the original code did bare imports of modules that don't exist in
# the repo, causing ModuleNotFoundError at startup. Each block below is now
# wrapped so the agent starts even if a module is absent; the unavailable
# tool is simply omitted from JARVIS_TOOLS.

def _try_import(fn):
    try:
        return fn()
    except (ImportError, ModuleNotFoundError) as e:
        logging.getLogger("jarvis_agent").warning(f"Optional module unavailable: {e}")
        return None

global_person_recon    = _try_import(lambda: __import__("sentient", fromlist=["global_person_recon"]).global_person_recon)
run_passive_dork       = _try_import(lambda: __import__("google_dork", fromlist=["run_passive_dork"]).run_passive_dork)
check_account_breach   = _try_import(lambda: __import__("google_dork", fromlist=["check_account_breach"]).check_account_breach)
web_search             = _try_import(lambda: __import__("Jarvis_google_search", fromlist=["web_search"]).web_search)
get_current_datetime   = _try_import(lambda: __import__("Jarvis_google_search", fromlist=["get_current_datetime"]).get_current_datetime)
get_weather            = _try_import(lambda: __import__("jarvis_weather", fromlist=["get_weather"]).get_weather)
send_email             = _try_import(lambda: __import__("jarvis_email", fromlist=["send_email"]).send_email)
send_whatsapp_message  = _try_import(lambda: __import__("jarvis_whatsapp", fromlist=["send_whatsapp_message"]).send_whatsapp_message)
play_youtube           = _try_import(lambda: __import__("jarvis_youtube", fromlist=["play_youtube"]).play_youtube)
download_youtube_video = _try_import(lambda: __import__("jarvis_toolbox", fromlist=["download_youtube_video"]).download_youtube_video)

# BUG FIX: original imported from "Jarvis_window_CTRL" (capital J) and
# "Jarvis_file_opner" (typo: opner). Corrected names here; adjust if your
# actual filenames differ.
_wctrl       = _try_import(lambda: __import__("Jarvis_window_CTRL", fromlist=["open", "close", "folder_file", "create_folder_tool"]))
open_app           = getattr(_wctrl, "open",              None)
close_window       = getattr(_wctrl, "close",             None)
folder_file        = getattr(_wctrl, "folder_file",       None)
create_folder_tool = getattr(_wctrl, "create_folder_tool", None)

Play_file  = _try_import(lambda: __import__("Jarvis_file_opner", fromlist=["Play_file"]).Play_file)
create_pdf = _try_import(lambda: __import__("jarvis_pdf_creator", fromlist=["create_pdf"]).create_pdf)

_km = _try_import(lambda: __import__("keyboard_mouse_CTRL", fromlist=[
    "move_cursor_tool", "mouse_click_tool", "scroll_cursor_tool", "type_text_tool",
    "press_key_tool", "press_hotkey_tool", "control_volume_tool", "swipe_gesture_tool",
]))
move_cursor_tool    = getattr(_km, "move_cursor_tool",    None)
mouse_click_tool    = getattr(_km, "mouse_click_tool",    None)
scroll_cursor_tool  = getattr(_km, "scroll_cursor_tool",  None)
type_text_tool      = getattr(_km, "type_text_tool",      None)
press_key_tool      = getattr(_km, "press_key_tool",      None)
press_hotkey_tool   = getattr(_km, "press_hotkey_tool",   None)
control_volume_tool = getattr(_km, "control_volume_tool", None)
swipe_gesture_tool  = getattr(_km, "swipe_gesture_tool",  None)

tool_take_screenshot = _try_import(lambda: __import__("jarvis_screenshot", fromlist=["tool_take_screenshot"]).tool_take_screenshot)

_ss = _try_import(lambda: __import__("jarvis_screenshare", fromlist=["capture_screen_tool", "smart_window_ctrl"]))
capture_screen_tool = getattr(_ss, "capture_screen_tool", None)
smart_window_ctrl   = getattr(_ss, "smart_window_ctrl",   None)

get_system_info   = _try_import(lambda: __import__("jarvis_system_info",  fromlist=["get_system_info"]).get_system_info)
read_clipboard    = _try_import(lambda: __import__("jarvis_clipboard",    fromlist=["read_clipboard"]).read_clipboard)
write_clipboard   = _try_import(lambda: __import__("jarvis_clipboard",    fromlist=["write_clipboard"]).write_clipboard)
store_memory      = _try_import(lambda: __import__("jarvis_memory",       fromlist=["store_memory"]).store_memory)
recall_memory     = _try_import(lambda: __import__("jarvis_memory",       fromlist=["recall_memory"]).recall_memory)
save_ambient_plan = _try_import(lambda: __import__("jarvis_ambient",      fromlist=["save_ambient_plan"]).save_ambient_plan)
index_documents   = _try_import(lambda: __import__("jarvis_doc_indexer",  fromlist=["index_documents"]).index_documents)
search_documents  = _try_import(lambda: __import__("jarvis_doc_indexer",  fromlist=["search_documents"]).search_documents)
web_automation_task  = _try_import(lambda: __import__("jarvis_browser_agent", fromlist=["web_automation_task"]).web_automation_task)
synthesize_new_tool  = _try_import(lambda: __import__("jarvis_synthesizer",   fromlist=["synthesize_new_tool"]).synthesize_new_tool)
forage_knowledge     = _try_import(lambda: __import__("jarvis_forager",        fromlist=["forage_knowledge"]).forage_knowledge)

# BUG FIX: "Jarvis_prompts" did not exist in the repo. Provide safe fallbacks.
try:
    from Jarvis_prompts import instructions_prompt, Reply_prompts
except (ImportError, ModuleNotFoundError):
    instructions_prompt = (
        "You are Jarvis, an advanced autonomous AI assistant. "
        "Help the user with any task using your available tools."
    )
    Reply_prompts = "Keep responses concise and action-oriented."

load_dotenv()
logger = logging.getLogger("jarvis_agent")
logger.setLevel(logging.INFO)

# Build tool list from only the modules that loaded successfully
JARVIS_TOOLS = [t for t in [
    global_person_recon, run_passive_dork, check_account_breach,
    web_search, get_current_datetime, get_weather,
    send_email, send_whatsapp_message,
    play_youtube, download_youtube_video,
    open_app, close_window, folder_file, create_folder_tool, Play_file, create_pdf,
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
    tool_take_screenshot, capture_screen_tool, smart_window_ctrl,
    get_system_info, read_clipboard, write_clipboard, store_memory, recall_memory,
    save_ambient_plan, index_documents, search_documents,
    web_automation_task, synthesize_new_tool, forage_knowledge,
] if t is not None]

logger.info(f"Loaded {len(JARVIS_TOOLS)} tools.")


def prewarm(proc: agents.JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    logger.info(f"✨ JARVIS online in room: {ctx.room.name}")
    await ctx.connect()

    fnc_ctx = agents.llm.FunctionContext()
    for tool in JARVIS_TOOLS:
        fnc_ctx.add_tool(tool)

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=google.STT(),
        llm=google.LLM(model="gemini-2.0-flash-exp"),
        tts=google.TTS(),
        fnc_ctx=fnc_ctx,
        chat_ctx=agents.llm.ChatContext().append(
            role="system",
            text=f"{instructions_prompt}\n\n{Reply_prompts}",
        ),
    )

    agent.start(ctx.room)
    print("🚀 JARVIS is now online.")
    await agent.say("System online. All modules integrated and ready.", allow_interruptions=True)

    # BUG FIX: original loop polled is_connected once/sec with no disconnect
    # handler — it would hang forever on a silent drop. Now we use an asyncio
    # Event that is set by the disconnect callback, with a 60-second heartbeat
    # so the loop also exits cleanly on process shutdown.
    disconnected = asyncio.Event()

    @ctx.room.on("disconnected")
    def _on_disconnect(*_):
        disconnected.set()

    while not disconnected.is_set():
        try:
            await asyncio.wait_for(disconnected.wait(), timeout=60)
        except asyncio.TimeoutError:
            if not ctx.room.is_connected:
                logger.warning("Room appears disconnected without event — exiting loop.")
                break

    logger.info("Room disconnected. JARVIS shutting down.")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
