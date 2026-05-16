import logging
from livekit.agents import function_tool
from duckduckgo_search import DDGS

logger = logging.getLogger("JarvisForager")

@function_tool
async def forage_knowledge(topic: str, goal: str) -> str:
    """
    Performs deep 'Epistemic Foraging' to find research gaps and scientific intelligence.
    Combines web data with Arxiv-specific queries.
    
    Args:
        topic (str): The scientific or technical topic to research.
        goal (str): The specific research question or system goal (e.g., 'Optimize Active Inference loop').
    """
    logger.info(f"Jarvis is foraging intelligence on: {topic}")
    
    # Targeting scientific sources
    queries = [
        f'"{topic}" site:arxiv.org OR site:scholar.google.com "research gap" OR "future work"',
        f'"{topic}" "{goal}" advanced implementation GitHub OR documentation',
        f'latest breakthroughs in "{topic}" 2024-2025'
    ]
    
    results = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                search_res = list(ddgs.text(q, max_results=3))
                results.extend(search_res)
    except Exception as e:
        logger.error(f"Foraging search failed: {e}")
        return f"Sir, searching blocks mein kuch issue aa raha hai. Research throttled ho gayi hai."

    if not results:
        return f"Sir, maine global indexes check kiye par '{topic}' par koi significant research gap nahi mila."

    intelligence_report = f"🧪 **Intelligence Report: {topic}**\n\n"
    intelligence_report += f"**Goal Focus:** {goal}\n\n"
    intelligence_report += "Sir, maine kuch potential leads search kiye hain:\n"
    
    for i, r in enumerate(results, 1):
        title = r.get('title', 'Unknown Title')
        link = r.get('href', '#')
        snippet = r.get('body', 'No detail available.')
        intelligence_report += f"{i}. **{title}**\n   - Link: {link}\n   - Insight: {snippet[:200]}...\n\n"

    intelligence_report += "Sir, kya main inme se kisi paper ka deep summary nikaloon?"
    
    return intelligence_report
