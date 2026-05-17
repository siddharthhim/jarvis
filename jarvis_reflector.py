"""
jarvis_reflector.py — Self-Improvement Loop for Jarvis

How it works:
1. Every tool call outcome (success/failure + result) is logged to jarvis_action_log.jsonl
2. log_action() is called from agent.py after each tool completes
3. reflect_on_performance() reads the last N actions, asks Gemini what Jarvis should do
   differently, and writes insights to self_notes.txt
4. self_notes.txt is injected into the system prompt on next startup so Jarvis actually
   improves its behavior over time
"""

import os
import json
import logging
from datetime import datetime
from livekit.agents import function_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("JarvisReflector")

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

_BASE_DIR     = os.path.dirname(__file__)
_ACTION_LOG   = os.path.join(_BASE_DIR, "jarvis_action_log.jsonl")
_SELF_NOTES   = os.path.join(_BASE_DIR, "self_notes.txt")

# How many recent actions to send to the reflection prompt
_REFLECTION_WINDOW = 15


# ── Core logging (called from agent.py, not an AI tool) ───────────────────

def log_action(tool_name: str, args: dict, result: str, success: bool):
    """
    Logs a single tool call outcome.
    Call this from agent.py after every function_tool returns.

    Args:
        tool_name: Name of the tool that was called.
        args:      Dict of arguments passed to the tool.
        result:    String result returned by the tool.
        success:   True if the tool completed without error.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "args": args,
        "result": result[:300],   # truncate to keep log compact
        "success": success,
    }
    try:
        with open(_ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Could not log action: {e}")


def load_self_notes() -> str:
    """
    Returns Jarvis's self-generated improvement notes as a string.
    Injected into the system prompt in agent.py so every session
    benefits from prior reflections.
    """
    if not os.path.exists(_SELF_NOTES):
        return ""
    try:
        with open(_SELF_NOTES, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _load_recent_actions(n: int = _REFLECTION_WINDOW) -> list[dict]:
    """Read the last N actions from the action log."""
    if not os.path.exists(_ACTION_LOG):
        return []
    try:
        with open(_ACTION_LOG, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        recent = lines[-n:]
        return [json.loads(l) for l in recent]
    except Exception as e:
        logger.warning(f"Could not load action log: {e}")
        return []


# ── AI Tools ───────────────────────────────────────────────────────────────

@function_tool
async def reflect_on_performance() -> str:
    """
    Analyzes Jarvis's recent tool calls and generates self-improvement notes.
    Jarvis will critique its own behavior and write better strategies to disk.
    These notes are automatically included in the system prompt on next startup.

    Use when the user says 'reflect on your performance', 'how can you improve?',
    'analyze your recent actions', or after completing a large task.
    """
    actions = _load_recent_actions()
    if not actions:
        return "Sir, abhi tak koi actions log nahi hain. Pehle kuch tools use karein."

    # Format action log for the prompt
    action_text = ""
    for a in actions:
        status = "✅" if a["success"] else "❌"
        action_text += (
            f"{status} [{a['timestamp'][:16]}] Tool: {a['tool']}\n"
            f"   Args: {json.dumps(a['args'], ensure_ascii=False)[:120]}\n"
            f"   Result: {a['result'][:150]}\n\n"
        )

    # Load existing notes so reflection is cumulative
    existing_notes = load_self_notes()

    prompt = f"""
You are Jarvis's self-improvement engine. Analyze the following recent actions and generate concrete behavioral improvements.

RECENT ACTIONS:
{action_text}

PREVIOUS SELF-NOTES (already known):
{existing_notes if existing_notes else "None yet."}

Your task:
1. Identify patterns in failures or inefficiencies.
2. Identify what worked well.
3. Write 3-5 NEW concrete behavioral rules Jarvis should follow going forward.
4. Write in first person ("I should...", "When X happens, I will...").
5. Be specific and actionable. Avoid vague advice.
6. Include the date so improvements are tracked over time.
7. Respond in Hinglish to match Jarvis's personality.

Output format:
--- Self-Improvement Notes [{datetime.now().strftime('%Y-%m-%d')}] ---
[your notes here]
"""

    try:
        response = await _llm.ainvoke(prompt)
        new_notes = response.content.strip()

        # Append to existing notes (cumulative improvement)
        with open(_SELF_NOTES, "a", encoding="utf-8") as f:
            f.write("\n\n" + new_notes)

        logger.info("Self-improvement notes updated.")
        return (
            f"🧠 Sir, maine apni performance analyze ki. Yeh rahi insights:\n\n"
            f"{new_notes}\n\n"
            f"✅ Yeh notes save ho gaye hain. Next session mein main automatically better perform karunga."
        )

    except Exception as e:
        logger.exception(f"Reflection failed: {e}")
        return f"❌ Reflection mein error: {e}"


@function_tool
async def show_self_notes() -> str:
    """
    Displays Jarvis's accumulated self-improvement notes.
    Use when the user asks 'what have you learned?', 'show your notes', etc.
    """
    notes = load_self_notes()
    if not notes:
        return "Sir, abhi tak koi self-improvement notes nahi hain. 'reflect_on_performance' use karein."
    return f"📓 Jarvis's Self-Notes:\n\n{notes}"


@function_tool
async def show_action_log(last_n: int = 10) -> str:
    """
    Shows Jarvis's recent tool call history with success/failure status.
    Useful for debugging or reviewing what Jarvis has been doing.

    Args:
        last_n (int): Number of recent actions to show (default 10).
    """
    actions = _load_recent_actions(last_n)
    if not actions:
        return "Sir, action log abhi khali hai."

    lines = [f"📋 Last {len(actions)} Actions:\n"]
    for a in actions:
        icon = "✅" if a["success"] else "❌"
        lines.append(
            f"{icon} {a['timestamp'][:16]} | {a['tool']}\n"
            f"   → {a['result'][:100]}"
        )
    return "\n".join(lines)


@function_tool
async def clear_action_log() -> str:
    """
    Clears the action log. Use when starting fresh or the log gets too large.
    """
    try:
        if os.path.exists(_ACTION_LOG):
            os.remove(_ACTION_LOG)
        return "🗑️ Action log clear kar diya Sir."
    except Exception as e:
        return f"❌ Log clear nahi ho paaya: {e}"
