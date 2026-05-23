import os
import asyncio
import logging
from livekit.agents import function_tool
from browser_use import Agent, Browser
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── LLM init ──────────────────────────────────────────────────────────────
# FIX: Removed ChatGoogleGenerativeAIWithProvider subclass — it added an
# undeclared Pydantic field which caused a validation error on instantiation,
# silently setting _llm = None and disabling all browser automation.
try:
    _llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
except Exception as e:
    logger.error(f"Failed to initialize LLM for Browser Agent: {e}")
    _llm = None

# Max seconds a browser task is allowed to run before we give up
_BROWSER_TIMEOUT_SECONDS = 120


@function_tool
async def web_automation_task(goal: str) -> str:
    """
    Performs autonomous web browsing tasks using AI and Playwright.

    Args:
        goal (str): Natural language description of the web task to perform.
    """
    if not _llm:
        return "❌ Sir, browser capabilities not configured. Please check GOOGLE_API_KEY."

    logger.info(f"Browser Agent starting task: {goal}")

    browser = Browser()
    try:
        # FIX: browser.close() is now in finally — always runs even on exception.
        # FIX: asyncio.wait_for enforces a timeout so a stuck task can't block the event loop.
        agent = Agent(task=goal, llm=_llm, browser=browser)

        result = await asyncio.wait_for(
            agent.run(),
            timeout=_BROWSER_TIMEOUT_SECONDS,
        )

        if result and hasattr(result, "final_result") and result.final_result():
            return f"✅ Web Task Complete, Sir. Result: {result.final_result()}"
        else:
            return "✅ Task done, Sir, but could not extract specific data from the page."

    except asyncio.TimeoutError:
        logger.error(f"Browser Agent timed out after {_BROWSER_TIMEOUT_SECONDS}s for task: {goal}")
        return f"❌ Sir, browser task timed out after {_BROWSER_TIMEOUT_SECONDS} seconds."
    except Exception as e:
        logger.error(f"Browser Agent Exception: {e}")
        return f"❌ Error during web automation, Sir: {e}"
    finally:
        # FIX: This now always runs — no browser process leaks.
        try:
            await browser.close()
        except Exception as close_err:
            logger.warning(f"Browser close error (non-critical): {close_err}")
