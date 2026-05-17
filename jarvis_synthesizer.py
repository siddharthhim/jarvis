import os
import re
import ast
import sys
import logging
import asyncio
import importlib
import importlib.util
from livekit.agents import function_tool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("JarvisSynthesizer")

CUSTOM_TOOLS_DIR = os.path.join(os.path.dirname(__file__), "jarvis_tools_custom")
os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)

# Add custom tools dir to sys.path once so importlib can find modules there
if CUSTOM_TOOLS_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_TOOLS_DIR)

# ── In-memory registry of hot-loaded tools ────────────────────────────────────
# Maps tool_name → the actual function object so we can re-register on demand
_loaded_custom_tools: dict = {}


def _get_llm():
    """Lazy LLM init — missing API key fails at call time, not import time."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not set.")
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)


def _strip_markdown(code: str) -> str:
    """
    Robustly strip markdown code fences regardless of capitalisation or
    trailing whitespace that Gemini occasionally produces.
    """
    # Remove ```python, ```Python, ```py, ``` at start
    code = re.sub(r"^```[a-zA-Z]*\s*\n?", "", code.strip())
    # Remove trailing ```
    code = re.sub(r"\n?```\s*$", "", code.strip())
    return code.strip()


def _is_safe_code(code: str) -> tuple[bool, str]:
    """
    Basic static safety check using Python's AST.
    Rejects generated code that contains obviously dangerous calls.
    Returns (is_safe, reason).
    """
    BANNED_CALLS = {
        "eval", "exec", "compile", "__import__",
        "os.remove", "os.rmdir", "shutil.rmtree",
        "subprocess.call", "subprocess.run", "subprocess.Popen",
    }
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError in generated code: {e}"

    for node in ast.walk(tree):
        # Check direct function calls like eval(), exec()
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                # e.g. os.remove
                if isinstance(func.value, ast.Name):
                    name = f"{func.value.id}.{func.attr}"
            if name in BANNED_CALLS:
                return False, f"Dangerous call detected: {name}()"

    return True, "ok"


def _hot_load_tool(file_path: str, name: str):
    """
    Dynamically import a synthesized tool module and return the
    @function_tool decorated function inside it.
    Returns the tool function or None on failure.
    """
    try:
        spec = importlib.util.spec_from_file_location(name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Expect the function to share the same name as the file
        fn = getattr(module, name, None)
        if fn is None:
            # Fall back: grab the first callable that isn't dunder
            for attr in dir(module):
                obj = getattr(module, attr)
                if callable(obj) and not attr.startswith("_"):
                    fn = obj
                    break
        if fn:
            _loaded_custom_tools[name] = fn
            logger.info(f"✅ Hot-loaded custom tool: {name}")
        return fn
    except Exception as e:
        logger.error(f"Hot-load failed for {name}: {e}")
        return None


def load_custom_tools() -> list:
    """
    Load all previously synthesized tools from the custom tools directory.
    Called once at agent startup so existing tools survive restarts.
    Returns a list of tool functions ready to be added to fnc_ctx.
    """
    tools = []
    if not os.path.isdir(CUSTOM_TOOLS_DIR):
        return tools
    for fname in os.listdir(CUSTOM_TOOLS_DIR):
        if fname.endswith(".py") and not fname.startswith("_"):
            name = fname[:-3]
            fpath = os.path.join(CUSTOM_TOOLS_DIR, fname)
            fn = _hot_load_tool(fpath, name)
            if fn:
                tools.append(fn)
    return tools


@function_tool
async def synthesize_new_tool(name: str, description: str) -> str:
    """
    Autonomously creates a new Python tool for Jarvis based on a description,
    saves it, safety-checks it, and hot-loads it immediately — no restart needed.

    Args:
        name (str): Short snake_case name for the tool (e.g. 'disk_usage_checker').
        description (str): Detailed instruction on what the tool should do.
    """
    logger.info(f"Jarvis synthesizing tool: {name}")

    sys_prompt = f"""You are the 'Self-Coding' engine of Jarvis.
Write a high-quality Python tool using the livekit-agents library.

STRICT RULES:
1. Output ONLY raw Python code. No markdown fences, no explanations.
2. Import 'logging' and 'from livekit.agents import function_tool'.
3. The main function MUST be decorated with '@function_tool'.
4. The function MUST be 'async'.
5. Include a clear docstring describing what it does and its Args.
6. Wrap all logic in try-except blocks.
7. Use Hinglish in return strings (e.g., 'Sir, kaam ho gaya!').
8. The function name MUST be exactly: {name}
9. Use only standard libraries (os, psutil, requests, etc.).
10. Never use eval(), exec(), subprocess, os.remove, or shutil.rmtree.

Tool Goal: {description}
"""

    try:
        llm = _get_llm()
    except EnvironmentError as e:
        return f"❌ LLM config error: {e}"

    try:
        response = await llm.ainvoke(sys_prompt)
        code = _strip_markdown(response.content)

        if not code.strip():
            return "❌ LLM returned empty code Sir। Please try again with a clearer description."

        # ── Safety check before writing to disk ──────────────────────────────
        is_safe, reason = _is_safe_code(code)
        if not is_safe:
            logger.warning(f"Generated code for '{name}' failed safety check: {reason}")
            return (
                f"⚠️ Sir, generated tool '{name}' safety check fail hua:\n"
                f"Reason: {reason}\n"
                f"Maine ise save nahi kiya. Please description refine karein."
            )

        file_path = os.path.join(CUSTOM_TOOLS_DIR, f"{name}.py")
        def _write():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        await asyncio.to_thread(_write)

        # ── Hot-load immediately — no restart needed ──────────────────────────
        fn = _hot_load_tool(file_path, name)
        if fn:
            return (
                f"✅ Sir, '{name}' tool synthesize aur load ho gaya hai! "
                f"Main ise abhi use kar sakta hoon बिना restart ke।"
            )
        else:
            return (
                f"✅ Sir, '{name}' tool save ho gaya hai, "
                f"par hot-load nahi hua। Restart ke baad available hoga।"
            )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return f"❌ Maafi chahta hoon Sir, tool synthesize nahi ho paaya: {e}"


if __name__ == "__main__":
    async def test():
        res = await synthesize_new_tool(
            "hello_tool",
            "A simple tool that returns a greeting message."
        )
        print(res)
    asyncio.run(test())
