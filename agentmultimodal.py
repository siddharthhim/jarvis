import os
import asyncio
import logging
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, cli
from livekit.plugins import google, noise_cancellation, silero

# Same imports as agent.py (truncated for brevity, but include all)
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
logger = logging.getLogger("jarvis_multimodal")
logger.setLevel(logging.INFO)

JARVIS_TOOLS = [  # Same list as above
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

class JarvisAssistant(Agent):
    def __init__(self) -> None:
        full_instructions = f"{instructions_prompt}\n\n{Reply_prompts}"
        super().__init__(
            instructions=full_instructions,
            tools=JARVIS_TOOLS,
        )

server = AgentServer()

@server.rtc_session(agent_name="jarvis-multimodal")
async def jarvis_agent(ctx: agents.JobContext):
    logger.info(f"🚀 Multimodal JARVIS online in room: {ctx.room.name}")
    await ctx.connect()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="charon",
            temperature=0.8,
        ),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=JarvisAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await session.generate_reply(instructions="Greet the user and report that all modules are online.")

    while ctx.room.is_connected:
        await asyncio.sleep(1)

if __name__ == "__main__":
    cli.run_app(server)