import os
import asyncio
import logging
from livekit.agents import function_tool
from browser_use import Agent, Browser
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ChatGoogleGenerativeAIWithProvider(ChatGoogleGenerativeAI):
    provider: str = 'google'

try:
    _llm = ChatGoogleGenerativeAIWithProvider(model='gemini-2.5-flash', api_key=os.getenv('GOOGLE_API_KEY'))
except Exception as e:
    logger.error(f"Failed to initialize LLM for Browser: {e}")
    _llm = None

@function_tool
async def web_automation_task(goal: str) -> str:
    """
    Performs autonomous web browsing tasks using AI and Playwright.
    """
    if not _llm:
        return "Web capabilities not configured. Please check API key."
    logger.info(f"Browser Agent starting task: {goal}")
    try:
        browser = Browser()
        agent = Agent(task=goal, llm=_llm, browser=browser)
        result = await agent.run()
        await browser.close()
        if result and hasattr(result, 'final_result') and result.final_result():
            return f"Web Task Complete. Result: {result.final_result()}"
        else:
            return "Task done but could not extract specific data."
    except Exception as e:
        logger.error(f"Browser Agent Exception: {e}")
        return f"Error during web automation: {e}"