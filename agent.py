"""
agent.py — Jarvis Main Voice Pipeline
Integrates: Goal-Directed Reasoning, Self-Improvement Loop, Multi-Agent Collaboration
"""

import logging
import os
import sys
import importlib
import asyncio
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, VoicePipelineAgent
from livekit.plugins import google, silero

# ── Core tool imports ──────────────────────────────────────────────────────
from sentient import global_person_recon
from google_dork import run_passive_dork, check_account_breach
from Jarvis_google_search import web_search, get_current_datetime
from jarvis_weather import get_weather
from jarvis_email import send_email
from jarvis_whatsapp import send_whatsapp_message
from jarvis_youtube import play_youtube
from jarvis_toolbox import download_youtube_video
from jarvis_window_CTRL import open as open_app, close as close_window, folder_file, create_folder_tool
from jarvis_file_opener import Play_file
from jarvis_pdf_creator import create_pdf
from keyboard_mouse_CTRL import (
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool
)
from jarvis_screenshot import tool_take_screenshot
from jarvis_screenshare import capture_screen_tool, smart_window_ctrl
from jarvis_system_info import get_system_info
from jarvis_clipboard import read_clipboard, write_clipboard
from jarvis_memory import store_memory, recall_memory, log_transcript
from jarvis_ambient import save_ambient_plan
from jarvis_doc_indexer import index_documents, search_documents
from jarvis_browser_agent import web_automation_task
from jarvis_synthesizer import synthesize_new_tool
from jarvis_forager import forage_knowledge
from Jarvis_prompts import instructions_prompt, Reply_prompts

# ── NEW: Goal-Directed Reasoning ──────────────────────────────────────────
from jarvis_planner import create_goal_plan, execute_plan, show_current_plan, abandon_plan

# ── NEW: Self-Improvement Loop ────────────────────────────────────────────
from jarvis_reflector import (
    reflect_on_performance, show_self_notes, show_action_log,
    clear_action_log, log_action, load_self_notes
)

# ── NEW: Multi-Agent Collaboration ────────────────────────────────────────
from jarvis_orchestrator import multi_agent_task, list_available_agents, research_and_code

load_dotenv()

logger = logging.getLogger("jarvis_agent")
logger.setLevel(logging.INFO)

CUSTOM_TOOLS_DIR = os.path.join(os.path.dirname(__file__), "jarvis_tools_custom")


# ── Custom Tool Hot-Loader ─────────────────────────────────────────────────
def load_custom_tools() -> list:
    custom_tools = []
    if not os.path.isdir(CUSTOM_TOOLS_DIR):
        return custom_tools
    sys.path.insert(0, CUSTOM_TOOLS_DIR)
    for filename in os.listdir(CUSTOM_TOOLS_DIR):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        module_name = filename[:-3]
        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                if callable(obj) and hasattr(obj, "__livekit_tool__"):
                    custom_tools.append(obj)
                    logger.info(f"✅ Custom tool loaded: {attr_name}")
        except Exception as e:
            logger.warning(f"⚠️ Custom tool '{module_name}' skipped: {e}")
    return custom_tools


# ── All Tools ──────────────────────────────────────────────────────────────
JARVIS_TOOLS = [
    # Core
    global_person_recon, run_passive_dork, check_account_breach,
    web_search, get_current_datetime, get_weather,
    send_email, send_whatsapp_message,
    play_youtube, download_youtube_video,
    open_app, close_window, folder_file, create_folder_tool, Play_file, create_pdf,
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
    tool_take_screenshot, capture_screen_tool, smart_window_ctrl,
    get_system_info, read_clipboard, write_clipboard,
    store_memory, recall_memory,
    save_ambient_plan, index_documents, search_documents,
    web_automation_task, synthesize_new_tool, forage_knowledge,

    # NEW: Goal-Directed Reasoning
    create_goal_plan, execute_plan, show_current_plan, abandon_plan,

    # NEW: Self-Improvement
    reflect_on_performance, show_self_notes, show_action_log, clear_action_log,

    # NEW: Multi-Agent Collaboration
    multi_agent_task, list_available_agents, research_and_code,
]


def prewarm(proc: agents.JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    logger.info(f"✨ JARVIS online — Room: {ctx.room.name}")
    await ctx.connect()

    # Inject self-improvement notes into the system prompt
    self_notes = load_self_notes()
    extra_context = ""
    if self_notes:
        extra_context = f"\n\n--- JARVIS SELF-IMPROVEMENT NOTES ---\n{self_notes}\n--- END NOTES ---"
        logger.info("Self-improvement notes injected into system prompt.")

    system_prompt = f"{instructions_prompt}\n\n{Reply_prompts}{extra_context}"

    fnc_ctx = agents.llm.FunctionContext()
    for tool in JARVIS_TOOLS:
        fnc_ctx.add_tool(tool)
    for tool in load_custom_tools():
        fnc_ctx.add_tool(tool)

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=google.STT(),
        llm=google.LLM(model="gemini-2.0-flash-exp"),
        tts=google.TTS(),
        fnc_ctx=fnc_ctx,
        chat_ctx=agents.llm.ChatContext().append(
            role="system",
            text=system_prompt,
        ),
    )

    # Transcript logging
    @agent.on("user_speech_committed")
    def on_user_speech(msg):
        log_transcript(msg.content, speaker="User")

    @agent.on("agent_speech_committed")
    def on_agent_speech(msg):
        log_transcript(msg.content, speaker="Jarvis")

    # Self-improvement: log every tool call outcome automatically
    @agent.on("function_calls_collected")
    def on_tool_calls(calls):
        for call in calls:
            logger.info(f"Tool called: {call.function_name}")

    @agent.on("function_calls_finished")
    def on_tool_finished(calls):
        for call in calls:
            success = not str(call.result).startswith("❌")
            log_action(
                tool_name=call.function_name,
                args=call.arguments if isinstance(call.arguments, dict) else {},
                result=str(call.result),
                success=success,
            )

    agent.start(ctx.room)

    print("🚀 JARVIS online. Goal reasoning + multi-agent + self-improvement active.")
    await agent.say(
        "System online. Goal planning, multi-agent collaboration, and self-improvement modules are active.",
        allow_interruptions=True,
    )

    await ctx.room.wait_disconnected()
    logger.info("Room disconnected. Jarvis shutting down.")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
