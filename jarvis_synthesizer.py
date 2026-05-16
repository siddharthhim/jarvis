import os
import logging
import asyncio
from livekit.agents import function_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("JarvisSynthesizer")

# Configuration
CUSTOM_TOOLS_DIR = os.path.join(os.path.dirname(__file__), "jarvis_tools_custom")
os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)

# Initialize LLM
_llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=os.getenv('GOOGLE_API_KEY'))

@function_tool
async def synthesize_new_tool(name: str, description: str) -> str:
    """
    Autonomously creates a new Python tool for Jarvis based on a description.
    The new tool will be saved and registered for use.
    
    Args:
        name (str): Short, descriptive name for the tool file (e.g., 'disk_usage_checker').
        description (str): Detailed instruction on what the tool should do.
    """
    logger.info(f"Jarvis is synthesizing a new tool: {name}")
    
    sys_prompt = f"""
    You are the 'Self-Coding' engine of Jarvis. 
    Your task is to write a high-quality, professional Python tool using the livekit-agents library.
    
    RULES:
    1. Only output the Python code. No markdown backticks, no explanations.
    2. Import 'logging' and from 'livekit.agents' import 'function_tool'.
    3. The function must be decorated with '@function_tool'.
    4. The function must be 'async'.
    5. Include a clear docstring with Args and what it does.
    6. Wrap logic in try-except blocks.
    7. Use Hinglish in the return string to match Jarvis's personality (e.g., 'Sir, check kijiye results aa gaye hain').
    8. The tool name must be '{name}'.
    9. Use standard libraries like 'os', 'psutil', 'requests', etc., which are already in requirements.txt.
    
    Tool Goal: {description}
    """
    
    try:
        response = await _llm.ainvoke(sys_prompt)
        code = response.content.strip()
        
        # Clean up any potential markdown formatting
        if code.startswith("```python"):
            code = code.replace("```python", "", 1)
        if code.endswith("```"):
            code = code.rsplit("```", 1)[0]
        code = code.strip()

        file_path = os.path.join(CUSTOM_TOOLS_DIR, f"{name}.py")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        logger.info(f"Tool {name} successfully synthesized at {file_path}")
        return f"✅ Sir, maine '{name}' tool synthesize kar liya hai. Restart ke baad main ise use kar paunga!"
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return f"❌ Maafi chahta hoon Sir, tool synthesize nahi ho paaya: {e}"

if __name__ == "__main__":
    # Test call
    async def test():
        res = await synthesize_new_tool("test_tool", "A tool that prints 'Hello World'")
        print(res)
    asyncio.run(test())
