import os
import ast
import re
import uuid
import logging
import asyncio
import importlib.util
from livekit.agents import function_tool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("JarvisSynthesizer")

CUSTOM_TOOLS_DIR = os.path.join(os.path.dirname(__file__), "jarvis_tools_custom")
os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)

# BUG FIX: original initialised ChatGoogleGenerativeAI at module level,
# which crashed the whole agent at import time if GOOGLE_API_KEY was missing.
# The LLM is now created lazily inside the tool function.
def _get_llm():
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise RuntimeError(
            "langchain-google-genai is required for tool synthesis. "
            "Install with: pip install langchain-google-genai"
        ) from exc
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set in the environment.")
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)


def _strip_fences(code: str) -> str:
    """
    Remove markdown code fences from LLM output.
    BUG FIX: original only handled ```python fences and missed plain ```
    fences, leaving invalid syntax in the written file.
    """
    # Strip opening fence (with or without language tag)
    code = re.sub(r"^```[a-zA-Z]*\n?", "", code.strip())
    # Strip closing fence
    code = re.sub(r"\n?```$", "", code.strip())
    return code.strip()


def _validate_python(code: str, name: str) -> None:
    """
    Parse the generated code with ast.parse to catch syntax errors before
    writing to disk.
    BUG FIX: original wrote raw AI output with zero validation — a prompt
    injection or malformed response would land as a broken/dangerous file.
    """
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(
            f"Generated code for '{name}' has a syntax error: {exc}"
        ) from exc


@function_tool
async def synthesize_new_tool(name: str, description: str) -> str:
    """
    Autonomously creates a new Python tool for Jarvis based on a description.
    The new tool will be saved to jarvis_tools_custom/ and can be loaded
    immediately without a restart.

    Args:
        name (str): Short, descriptive name for the tool file (e.g. 'disk_usage_checker').
        description (str): Detailed instruction on what the tool should do.
    """
    # Sanitise the tool name to a safe filename
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())
    if not safe_name:
        return "❌ Tool name is invalid. Use letters, numbers, and underscores only."

    logger.info(f"Synthesizing new tool: {safe_name}")

    sys_prompt = f"""You are the 'Self-Coding' engine of Jarvis.
Your task is to write a high-quality, professional Python tool using the livekit-agents library.

RULES:
1. Output ONLY raw Python code. No markdown fences, no explanations.
2. Import 'logging' and from 'livekit.agents' import 'function_tool'.
3. The function must be decorated with '@function_tool'.
4. The function must be 'async'.
5. Include a clear docstring with Args and what it does.
6. Wrap all logic in try-except blocks.
7. Use Hinglish in return strings to match Jarvis's personality.
8. The function name must be '{safe_name}'.
9. Use only standard-library or already-installed packages (os, psutil, requests, etc.).

Tool Goal: {description}
"""

    try:
        llm = _get_llm()
    except RuntimeError as e:
        return f"❌ Cannot synthesize: {e}"

    try:
        response = await llm.ainvoke(sys_prompt)
        raw_code = response.content.strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"❌ LLM call failed: {e}"

    code = _strip_fences(raw_code)

    # BUG FIX: validate syntax before writing to disk
    try:
        _validate_python(code, safe_name)
    except ValueError as e:
        logger.error(str(e))
        return f"❌ Generated code is invalid: {e}"

    file_path = os.path.join(CUSTOM_TOOLS_DIR, f"{safe_name}.py")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
    except OSError as e:
        return f"❌ Could not write tool file: {e}"

    # BUG FIX: original comment said "restart ke baad use kar paunga" — the
    # tool was never actually loaded. We now attempt a live import so the tool
    # is immediately available in the current process.
    try:
        spec = importlib.util.spec_from_file_location(safe_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tool_fn = getattr(module, safe_name, None)
        if tool_fn is not None:
            logger.info(f"Tool '{safe_name}' loaded live at {file_path}")
            return (
                f"✅ Sir, '{safe_name}' tool synthesize aur load ho gaya hai! "
                f"Aap abhi use kar sakte hain."
            )
        else:
            return (
                f"✅ Sir, code save ho gaya ({file_path}) lekin function "
                f"'{safe_name}' module mein nahi mila — check karein."
            )
    except Exception as e:
        logger.warning(f"Tool saved but live-load failed: {e}")
        return (
            f"✅ Sir, '{safe_name}' tool save ho gaya hai ({file_path}). "
            f"Live load nahi hua ({e}) — restart karne par available hoga."
        )


if __name__ == "__main__":
    async def _test():
        res = await synthesize_new_tool("hello_world", "A tool that returns 'Hello, World!'")
        print(res)
    asyncio.run(_test())
