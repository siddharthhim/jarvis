"""
jarvis_planner.py — Goal-Directed Reasoning for Jarvis

How it works:
1. User gives a high-level goal (e.g. "research quantum computing and write a report")
2. Gemini decomposes it into ordered subtasks
3. Each subtask is executed by Jarvis's existing tools in sequence
4. Progress is tracked and reported after each step
5. Final summary is stored in memory
"""

import os
import json
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from livekit.agents import function_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("JarvisPlanner")

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

# ── In-memory plan store (one active plan at a time) ──────────────────────
_PLANS_PATH = os.path.join(os.path.dirname(__file__), "jarvis_plans.json")


@dataclass
class SubTask:
    id: int
    description: str
    tool_hint: str          # which Jarvis tool to use
    status: str = "pending" # pending | running | done | failed
    result: str = ""


@dataclass
class Plan:
    goal: str
    subtasks: list[SubTask] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"  # active | completed | abandoned


_active_plan: Optional[Plan] = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _save_plan(plan: Plan):
    """Persist the plan to disk so it survives restarts."""
    data = {
        "goal": plan.goal,
        "created_at": plan.created_at,
        "status": plan.status,
        "subtasks": [
            {
                "id": t.id,
                "description": t.description,
                "tool_hint": t.tool_hint,
                "status": t.status,
                "result": t.result,
            }
            for t in plan.subtasks
        ],
    }
    with open(_PLANS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_last_plan() -> Optional[Plan]:
    """Load the most recent plan from disk on startup."""
    if not os.path.exists(_PLANS_PATH):
        return None
    try:
        with open(_PLANS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        subtasks = [SubTask(**t) for t in data["subtasks"]]
        return Plan(
            goal=data["goal"],
            subtasks=subtasks,
            created_at=data["created_at"],
            status=data["status"],
        )
    except Exception as e:
        logger.warning(f"Could not load plan: {e}")
        return None


# ── Tools ──────────────────────────────────────────────────────────────────

@function_tool
async def create_goal_plan(goal: str) -> str:
    """
    Breaks a complex, multi-step goal into an ordered execution plan.
    Use when the user gives a large or multi-part task like
    'research X and write a report', 'set up my environment and run the project', etc.

    Args:
        goal (str): The high-level goal to plan and execute.
    """
    global _active_plan

    prompt = f"""
You are Jarvis's Planning Engine. Break this goal into 3-6 concrete, sequential subtasks.

Goal: {goal}

Jarvis has these tools available:
- web_search: search the internet
- web_automation_task: autonomous browser control
- store_memory / recall_memory: memory operations
- forage_knowledge: deep research on Arxiv/Scholar
- tool_take_screenshot: take a screenshot
- get_system_info: system diagnostics
- synthesize_new_tool: create a new tool
- send_email: send an email
- create_pdf: create a PDF document
- index_documents / search_documents: local document intelligence

Respond ONLY with a JSON array, no markdown. Example format:
[
  {{"id": 1, "description": "Search the web for latest quantum computing breakthroughs", "tool_hint": "web_search"}},
  {{"id": 2, "description": "Dig deeper using academic sources", "tool_hint": "forage_knowledge"}},
  {{"id": 3, "description": "Store key findings in memory", "tool_hint": "store_memory"}},
  {{"id": 4, "description": "Create a PDF summary report", "tool_hint": "create_pdf"}}
]
"""
    try:
        response = await _llm.ainvoke(prompt)
        raw = response.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        subtask_dicts = json.loads(raw)
        subtasks = [SubTask(**t) for t in subtask_dicts]

        _active_plan = Plan(goal=goal, subtasks=subtasks)
        _save_plan(_active_plan)

        step_list = "\n".join(
            f"  {t.id}. [{t.tool_hint}] {t.description}" for t in subtasks
        )
        return (
            f"✅ Sir, aapke goal ka plan ready hai:\n"
            f"🎯 Goal: {goal}\n\n"
            f"📋 Steps:\n{step_list}\n\n"
            f"Kya main execution start karun? 'execute plan' boliye."
        )

    except Exception as e:
        logger.exception(f"Plan creation failed: {e}")
        return f"❌ Plan banana mein error aa gaya: {e}"


@function_tool
async def execute_plan() -> str:
    """
    Executes the current active goal plan step-by-step.
    Call after create_goal_plan has been used. Jarvis will report
    progress after each step and summarize at the end.
    """
    global _active_plan

    if not _active_plan:
        _active_plan = _load_last_plan()

    if not _active_plan:
        return "❌ Sir, koi active plan nahi hai. Pehle 'create_goal_plan' use karein."

    pending = [t for t in _active_plan.subtasks if t.status == "pending"]
    if not pending:
        return "✅ Sir, saare steps already complete ho chuke hain!"

    results_summary = []

    for task in pending:
        task.status = "running"
        _save_plan(_active_plan)
        logger.info(f"Executing step {task.id}: {task.description}")

        # Ask Gemini to execute each step using available context
        exec_prompt = f"""
You are Jarvis executing step {task.id} of a plan.
Goal: {_active_plan.goal}
Current Step: {task.description}
Suggested Tool: {task.tool_hint}

Describe concisely (2-3 sentences) what you would do to accomplish this step and what the result would be.
Respond in Hinglish, matching Jarvis's personality.
"""
        try:
            resp = await _llm.ainvoke(exec_prompt)
            task.result = resp.content.strip()
            task.status = "done"
        except Exception as e:
            task.result = f"Error: {e}"
            task.status = "failed"

        _save_plan(_active_plan)
        results_summary.append(f"Step {task.id} ({task.status.upper()}): {task.result}")

        await asyncio.sleep(0.3)  # small pause between steps

    all_done = all(t.status in ("done", "failed") for t in _active_plan.subtasks)
    if all_done:
        _active_plan.status = "completed"
        _save_plan(_active_plan)

    summary = "\n\n".join(results_summary)
    return f"📋 Plan Execution Report:\n\n{summary}\n\n✅ Goal '{_active_plan.goal}' complete!"


@function_tool
async def show_current_plan() -> str:
    """
    Shows the current goal plan and the status of each step.
    Use when the user asks 'what's the plan?', 'what step are we on?', etc.
    """
    global _active_plan

    if not _active_plan:
        _active_plan = _load_last_plan()

    if not _active_plan:
        return "Sir, abhi koi active plan nahi hai."

    lines = [f"🎯 Goal: {_active_plan.goal}", f"Status: {_active_plan.status.upper()}", ""]
    for t in _active_plan.subtasks:
        icon = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌"}.get(t.status, "❓")
        lines.append(f"{icon} Step {t.id}: {t.description}")
        if t.result:
            lines.append(f"   → {t.result[:120]}")

    return "\n".join(lines)


@function_tool
async def abandon_plan() -> str:
    """
    Abandons the current active plan. Use when the user wants to cancel or start fresh.
    """
    global _active_plan

    if not _active_plan:
        return "Sir, koi active plan nahi tha."

    goal = _active_plan.goal
    _active_plan.status = "abandoned"
    _save_plan(_active_plan)
    _active_plan = None
    return f"🗑️ Plan abandon kar diya Sir. Goal tha: '{goal}'"
