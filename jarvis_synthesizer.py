import os
import ast
import logging
import asyncio
from livekit.agents import function_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("JarvisSynthesizer")

CUSTOM_TOOLS_DIR = os.path.join(os.path.dirname(__file__), "jarvis_tools_custom")
os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


def _strip_markdown_fences(code: str) -> str:
    """
    FIX: Robust stripping of all markdown code fence variants.
    Handles ```python, ```, and leading/trailing whitespace.
    """
    lines = code.strip().splitlines()
    # Drop opening fence line (```python, ```py, ```, etc.)
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    # Drop closing fence line
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _validate_python(code: str, name: str) -> str | None:
    """
    FIX: AST parse check before writing to disk.
    Returns an error message if invalid, or None if valid.
    This prevents saving syntactically broken or injected code.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error in generated code: {e}"

    # Basic safety check: reject code that imports dangerous modules
    _BLOCKED_IMPORTS = {"subprocess", "shutil", "ctypes", "socket", "pty"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in getattr(node, "names", []):
                mod = alias.name.split(".")[0]
                if mod in _BLOCKED_IMPORTS:
                    return f"Generated code imports blocked module '{mod}' — rejected for safety."
        # Block calls to exec/eval/open in write mode as top-level statements
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ("exec", "eval"):
                return "Generated code contains exec/eval — rejected for safety."

    # Must contain the tool name as a defined function
    defined_funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef | ast.FunctionDef)]
    if name not in defined_funcs:
        return f"Generated code does not define a function named '{name}'."

    return None


@function_tool
async def synthesize_new_tool(name: str, description: str) -> str:
    """
    Autonomously creates a new Python tool for Jarvis based on a description.
    The new tool will be saved to jarvis_tools_custom/ for use after restart.

    Args:
        name (str): Short snake_case name for the tool (e.g., 'disk_usage_checker').
        description (str): Detailed description of what the tool should do.
    """
    # Sanitise name to prevent path traversal
    safe_name = "".join(c for c in name if c.isalnum() or c == "_")
    if not safe_name:
        return "❌ Sir, invalid tool name provided."

    logger.info(f"Jarvis synthesizing new tool: {safe_name}")

    sys_prompt = f"""
You are the 'Self-Coding' engine of Jarvis, an autonomous AI assistant.
Your task is to write a high-quality, professional Python tool.

STRICT RULES:
1. Output ONLY raw Python code. No markdown fences, no backticks, no preamble text.
2. Import 'logging' and from 'livekit.agents' import 'function_tool'.
3. The main function MUST be decorated with '@function_tool'.
4. The function MUST be 'async def {safe_name}(...)'.
5. Include a clear docstring with Args and description.
6. Wrap all logic in try-except blocks with specific exceptions.
7. Use Hinglish in return strings to match Jarvis personality.
8. Only use standard library modules or modules already in requirements.txt.
9. Do NOT use subprocess, shutil, socket, ctypes, exec, or eval.

Tool goal: {description}
"""

    try:
        response = await _llm.ainvoke(sys_prompt)
        raw_code = response.content.strip()

        # FIX: Robust markdown stripping
        code = _strip_markdown_fences(raw_code)

        # FIX: Validate before writing to disk
        validation_error = _validate_python(code, safe_name)
        if validation_error:
            logger.error(f"Tool synthesis validation failed: {validation_error}")
            return f"❌ Sir, synthesized tool failed validation: {validation_error}"

        file_path = os.path.join(CUSTOM_TOOLS_DIR, f"{safe_name}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        logger.info(f"Tool '{safe_name}' saved to {file_path}")
        return (
            f"✅ Sir, maine '{safe_name}' tool synthesize kar liya hai aur save ho gaya. "
            f"Restart ke baad main ise automatically load kar lunga!"
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return f"❌ Maafi chahta hoon Sir, tool synthesize nahi ho paaya: {e}"


if __name__ == "__main__":
    async def test():
        res = await synthesize_new_tool("hello_world", "A tool that returns a greeting message.")
        print(res)
    asyncio.run(test())
