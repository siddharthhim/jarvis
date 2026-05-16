import logging
import os
import asyncio
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, VoicePipelineAgent
from livekit.plugins import google, silero

from sentient import global_person_recon
from google_dork import run_passive_dork, check_account_breach
from Jarvis_google_search import web_search, get_current_datetime
from jarvis_weather import get_weather
from jarvis_email import send_email
from jarvis_whatsapp import send_whatsapp_message
from jarvis_youtube import play_youtube
from jarvis_toolbox import download_youtube_video
from Jarvis_window_CTRL import open as open_app, close as close_window, folder_file, create_folder_tool
from Jarvis_file_opner import Play_file
from jarvis_pdf_creator import create_pdf
from keyboard_mouse_CTRL import (
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool
)
from jarvis_screenshot import tool_take_screenshot
from jarvis_screenshare import capture_screen_tool, smart_window_ctrl
from jarvis_system_info import get_system_info
from jarvis_clipboard import read_clipboard, write_clipboard
from jarvis_memory import store_memory, recall_memory
from jarvis_ambient import save_ambient_plan
from jarvis_doc_indexer import index_documents, search_documents
from jarvis_browser_agent import web_automation_task
from jarvis_synthesizer import synthesize_new_tool
from jarvis_forager import forage_knowledge
from Jarvis_prompts import instructions_prompt, Reply_prompts

load_dotenv()
logger = logging.getLogger("jarvis_agent")
logger.setLevel(logging.INFO)

JARVIS_TOOLS = [
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
    web_automation_task, synthesize_new_tool, forage_knowledge
]

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

    while ctx.room.is_connected:
        await asyncio.sleep(1)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))