import asyncio
import logging
from livekit.agents import function_tool

logger = logging.getLogger("JarvisForager")

# Max searches per session to avoid burning through DuckDuckGo quota
_MAX_SEARCHES_PER_SESSION = 30
_search_count = 0


@function_tool
async def forage_knowledge(topic: str, goal: str) -> str:
    """
    Performs deep 'Epistemic Foraging' to find research gaps and scientific intelligence.
    Combines web data with Arxiv-specific queries.

    Args:
        topic (str): The scientific or technical topic to research.
        goal (str): The specific research question or objective
                    (e.g., 'Optimize Active Inference loop').
    """
    global _search_count

    if _search_count >= _MAX_SEARCHES_PER_SESSION:
        return (
            "⚠️ Sir, is session mein search limit reach ho gayi hai। "
            "Jarvis restart karein ya thodi der baad try karein।"
        )

    logger.info(f"Jarvis foraging intelligence on: {topic}")

    queries = [
        f'"{topic}" site:arxiv.org OR site:scholar.google.com "research gap" OR "future work"',
        f'"{topic}" "{goal}" advanced implementation GitHub OR documentation',
        f'latest breakthroughs "{topic}" 2024 2025',
    ]

    results = []

    def _run_searches():
        """Blocking DuckDuckGo search — runs in a thread."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            raise ImportError("duckduckgo-search not installed. Run: pip install duckduckgo-search")

        with DDGS() as ddgs:
            for q in queries:
                try:
                    batch = list(ddgs.text(q, max_results=3))
                    results.extend(batch)
                except Exception as e:
                    logger.warning(f"Search query failed (skipping): {q[:60]}… — {e}")

    try:
        await asyncio.to_thread(_run_searches)
        _search_count += len(queries)
    except ImportError as e:
        return f"❌ Sir, dependency missing: {e}"
    except Exception as e:
        logger.error(f"Foraging search failed: {e}")
        return (
            "❌ Sir, search mein kuch issue aa raha hai। "
            "Network check karein ya thodi der baad retry karein।"
        )

    if not results:
        return (
            f"🔍 Sir, maine global indexes check kiye par '{topic}' par "
            f"koi significant result nahi mila। "
            f"Try with a broader topic."
        )

    report = f"🧪 Intelligence Report: {topic}\n"
    report += f"Goal: {goal}\n"
    report += f"{'─' * 50}\n"
    report += "Sir, maine kuch potential leads dhunde hain:\n\n"

    for i, r in enumerate(results[:9], 1):  # Cap at 9 results in output
        title = r.get("title", "Unknown Title")
        link = r.get("href", "#")
        snippet = r.get("body", "No detail available.")[:200]
        report += f"{i}. {title}\n   Link: {link}\n   Insight: {snippet}...\n\n"

    report += "Sir, kya main inme se kisi paper ka deep summary nikaloon?"
    return report
