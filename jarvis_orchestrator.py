"""
jarvis_orchestrator.py — Multi-Agent Collaboration for Jarvis

How it works:
1. User gives a complex task requiring multiple parallel workstreams
2. Orchestrator asks Gemini to identify which specialist agents are needed
3. Three specialist sub-agents run concurrently via asyncio.gather():
   - ResearchAgent:  deep academic + web research
   - BrowserAgent:   autonomous browser automation
   - CoderAgent:     code generation and tool synthesis
   - AnalystAgent:   data analysis, summarization, report writing
4. All results are collected and synthesized into a final unified answer
5. The synthesis is stored in memory for future recall
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from livekit.agents import function_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("JarvisOrchestrator")

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))


# ── Sub-Agent Definitions ──────────────────────────────────────────────────

AGENT_REGISTRY = {
    "ResearchAgent": {
        "description": "Searches academic sources (Arxiv, Scholar) and the web for in-depth information.",
        "persona": "You are a meticulous research analyst. Your job is to find the most relevant, accurate, and recent information on the topic.",
    },
    "BrowserAgent": {
        "description": "Autonomously browses websites, fills forms, extracts data from live web pages.",
        "persona": "You are a skilled web navigator. Your job is to interact with live websites and extract structured data or complete web-based tasks.",
    },
    "CoderAgent": {
        "description": "Writes Python code, scripts, and technical solutions. Can synthesize new tools.",
        "persona": "You are an expert software engineer. Your job is to write clean, working code and technical solutions.",
    },
    "AnalystAgent": {
        "description": "Analyzes, summarizes, and synthesizes information. Writes reports and insights.",
        "persona": "You are a sharp analyst and writer. Your job is to synthesize information into clear, structured, actionable insights.",
    },
}


async def _run_sub_agent(agent_name: str, task: str, context: str) -> tuple[str, str]:
    """
    Runs a single specialist sub-agent asynchronously.

    Returns:
        Tuple of (agent_name, result_string)
    """
    agent_info = AGENT_REGISTRY.get(agent_name, {})
    persona = agent_info.get("persona", "You are a helpful assistant.")

    prompt = f"""
{persona}

OVERALL CONTEXT: {context}

YOUR SPECIFIC TASK: {task}

Instructions:
- Be thorough but concise (aim for 150-300 words).
- Structure your output clearly with short bullet points or paragraphs.
- Focus only on your assigned task — the orchestrator will combine all results.
- End with a one-line "KEY FINDING:" summary.
- Respond in Hinglish to match Jarvis's personality.
"""

    try:
        logger.info(f"[{agent_name}] Starting task: {task[:80]}")
        response = await _llm.ainvoke(prompt)
        result = response.content.strip()
        logger.info(f"[{agent_name}] Complete.")
        return (agent_name, result)
    except Exception as e:
        logger.error(f"[{agent_name}] Failed: {e}")
        return (agent_name, f"❌ Agent failed: {e}")


async def _orchestrate(task: str, agents_to_use: list[dict]) -> str:
    """
    Runs selected sub-agents in parallel and synthesizes their outputs.
    """
    # Run all agents concurrently
    coroutines = [
        _run_sub_agent(a["agent"], a["subtask"], task)
        for a in agents_to_use
    ]
    results = await asyncio.gather(*coroutines)

    # Format results for synthesis
    results_text = ""
    for agent_name, output in results:
        results_text += f"\n\n### {agent_name} Output:\n{output}"

    # Final synthesis pass
    synthesis_prompt = f"""
You are Jarvis synthesizing a multi-agent research report.

Original Task: {task}

Agent Outputs:
{results_text}

Your job:
1. Combine all agent outputs into ONE coherent, structured final answer.
2. Remove redundancy, resolve conflicts, highlight the most important findings.
3. Format with clear sections.
4. End with a "JARVIS VERDICT:" section — one paragraph with the final recommendation or conclusion.
5. Respond in Hinglish with Jarvis's personality (confident, helpful, slightly witty).
"""

    try:
        synthesis = await _llm.ainvoke(synthesis_prompt)
        return synthesis.content.strip()
    except Exception as e:
        # If synthesis fails, just return all raw results
        return f"⚠️ Synthesis partial:\n{results_text}"


# ── Main Tool ──────────────────────────────────────────────────────────────

@function_tool
async def multi_agent_task(task: str) -> str:
    """
    Deploys multiple specialist AI sub-agents in parallel to tackle a complex task.
    Best for tasks requiring research + coding + analysis + web browsing simultaneously.

    Examples: 'research quantum computing and write a Python simulation',
    'find the best AI papers this week and summarize them with code examples',
    'analyze this market and build a report with live data'.

    Args:
        task (str): The complex multi-faceted task to accomplish.
    """
    logger.info(f"Orchestrator received task: {task}")

    # Step 1: Ask Gemini which agents to use and what their subtasks are
    routing_prompt = f"""
You are Jarvis's task router. Analyze this task and decide which specialist agents are needed.

Task: {task}

Available agents:
{json.dumps({k: v['description'] for k, v in AGENT_REGISTRY.items()}, indent=2)}

Rules:
- Select 2-4 agents (no more — keep it focused).
- For each agent, write a specific subtask tailored to their specialty.
- Respond ONLY with a JSON array, no markdown:
[
  {{"agent": "ResearchAgent", "subtask": "specific thing for this agent to do"}},
  {{"agent": "CoderAgent", "subtask": "specific thing for this agent to do"}}
]
"""

    try:
        routing_response = await _llm.ainvoke(routing_prompt)
        raw = routing_response.content.strip()
        raw = raw.lstrip("```json").lstrip("```").rstrip("```").strip()
        agents_to_use = json.loads(raw)
    except Exception as e:
        logger.warning(f"Routing failed, defaulting to Research + Analyst: {e}")
        agents_to_use = [
            {"agent": "ResearchAgent", "subtask": f"Research this topic thoroughly: {task}"},
            {"agent": "AnalystAgent", "subtask": f"Analyze and summarize findings for: {task}"},
        ]

    agent_names = [a["agent"] for a in agents_to_use]
    logger.info(f"Deploying agents: {agent_names}")

    # Announce deployment
    agent_list = ", ".join(agent_names)

    # Step 2: Run all agents in parallel
    start_time = asyncio.get_event_loop().time()
    final_result = await _orchestrate(task, agents_to_use)
    elapsed = asyncio.get_event_loop().time() - start_time

    header = (
        f"🤖 Multi-Agent Task Complete!\n"
        f"⚡ Agents Used: {agent_list}\n"
        f"⏱️ Time: {elapsed:.1f}s\n"
        f"{'─' * 50}\n\n"
    )

    return header + final_result


@function_tool
async def list_available_agents() -> str:
    """
    Lists all available specialist sub-agents and their capabilities.
    Use when the user asks 'what agents do you have?', 'who can help with X?', etc.
    """
    lines = ["🤖 Available Jarvis Sub-Agents:\n"]
    for name, info in AGENT_REGISTRY.items():
        lines.append(f"• **{name}**: {info['description']}")
    lines.append("\nUse 'multi_agent_task' to deploy them on a complex task.")
    return "\n".join(lines)


@function_tool
async def research_and_code(topic: str, code_task: str) -> str:
    """
    Convenience shortcut: runs ResearchAgent and CoderAgent in parallel.
    ResearchAgent finds information, CoderAgent writes related code simultaneously.

    Args:
        topic (str): What to research.
        code_task (str): What code to write (related to the research).
    """
    agents_to_use = [
        {"agent": "ResearchAgent", "subtask": f"Research deeply: {topic}"},
        {"agent": "CoderAgent",    "subtask": f"Write code for: {code_task}"},
        {"agent": "AnalystAgent",  "subtask": f"Synthesize research findings and code purpose for: {topic} — {code_task}"},
    ]

    combined_task = f"Research '{topic}' and write code for '{code_task}'"
    result = await _orchestrate(combined_task, agents_to_use)

    return f"🔬 Research + Code Task Complete:\n\n{result}"
