import os
import asyncio
import logging
from livekit.agents import function_tool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_llm():
    """
    Lazy-initialize the LLM so a missing API key only fails when the tool
    is actually called, not at module-import time (which would crash the
    entire agent startup).
    """
    from browser_use import Agent, Browser
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY not set — browser agent cannot initialise."
        )

    # Subclass needed to satisfy browser-use's provider field validation
    class _ChatGoogleWithProvider(ChatGoogleGenerativeAI):
        provider: str = "google"

    return _ChatGoogleWithProvider(model="gemini-2.5-flash", api_key=api_key)


@function_tool
async def web_automation_task(goal: str) -> str:
    """
    Performs autonomous web browsing tasks using AI and Playwright.
    Use for tasks like 'fill out this form', 'search and summarise results',
    'log in and fetch data', or any multi-step web workflow.

    Args:
        goal (str): A plain-English description of the browsing task to complete.
    """
    # ── Lazy import so heavy Playwright deps don't slow startup ──────────────
    try:
        from browser_use import Agent, Browser
    except ImportError:
        return "❌ browser-use library not installed. Run: pip install browser-use"

    logger.info(f"Browser Agent starting task: {goal}")

    browser = None
    try:
        llm = _get_llm()
        browser = Browser()
        agent = Agent(task=goal, llm=llm, browser=browser)
        result = await agent.run()

        if result and hasattr(result, "final_result") and result.final_result():
            return f"✅ Web Task Complete Sir. Result: {result.final_result()}"
        return "✅ Task done Sir, but no specific data could be extracted."

    except EnvironmentError as e:
        logger.error(f"Browser Agent config error: {e}")
        return f"❌ Configuration error: {e}"
    except Exception as e:
        logger.error(f"Browser Agent Exception: {e}")
        return f"❌ Error during web automation Sir: {e}"
    finally:
        # ── Fixed: browser is ALWAYS closed, even on exceptions ───────────────
        if browser is not None:
            try:
                await browser.close()
                logger.info("Browser closed successfully.")
            except Exception as close_err:
                logger.warning(f"Browser close warning: {close_err}")
