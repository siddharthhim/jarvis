"""
jarvis_tool_registry.py
─────────────────────────────────────────────────────────────────────────────
Central tool registry for Jarvis.

Solves two main issues:
  1. Tools were scattered across 20+ files with no central manifest.
     Now a single place tracks every registered tool.
  2. Expensive / destructive tools had no confirmation gate or rate limit.
     This module adds both via decorators.

Usage in agent.py:
    from jarvis_tool_registry import JARVIS_TOOLS, get_tool_stats
"""

import time
import asyncio
import logging
import functools
from typing import Callable

logger = logging.getLogger("JarvisRegistry")

# ── In-memory rate-limit store ────────────────────────────────────────────────
# Maps tool_name → list of call timestamps (unix seconds)
_call_log: dict[str, list[float]] = {}

# ── Tool usage stats (reset on restart) ──────────────────────────────────────
_stats: dict[str, dict] = {}


def _record_call(name: str, success: bool, latency: float):
    entry = _stats.setdefault(name, {"calls": 0, "errors": 0, "total_ms": 0.0})
    entry["calls"] += 1
    if not success:
        entry["errors"] += 1
    entry["total_ms"] += latency * 1000


def get_tool_stats() -> str:
    """Returns a formatted string of tool usage stats."""
    if not _stats:
        return "Sir, abhi koi tool use nahi hua hai।"
    lines = ["📊 Tool usage stats:\n"]
    for name, s in sorted(_stats.items(), key=lambda x: -x[1]["calls"]):
        avg_ms = s["total_ms"] / s["calls"] if s["calls"] else 0
        lines.append(
            f"  {name}: {s['calls']} calls | "
            f"{s['errors']} errors | avg {avg_ms:.0f}ms"
        )
    return "\n".join(lines)


def rate_limited(max_calls: int = 5, window_seconds: int = 60):
    """
    Decorator — rejects calls if a tool is invoked more than `max_calls`
    times within `window_seconds`. Protects against runaway tool loops.
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            name = fn.__name__
            now = time.time()
            timestamps = _call_log.setdefault(name, [])
            # Drop timestamps outside window
            _call_log[name] = [t for t in timestamps if now - t < window_seconds]
            if len(_call_log[name]) >= max_calls:
                logger.warning(f"Rate limit hit for tool: {name}")
                return (
                    f"⚠️ Sir, '{name}' tool को {window_seconds}s में "
                    f"{max_calls} बार से ज़्यादा call नहीं कर सकते। "
                    f"Please थोड़ा wait करें।"
                )
            _call_log[name].append(now)
            start = time.time()
            try:
                result = await fn(*args, **kwargs)
                _record_call(name, True, time.time() - start)
                return result
            except Exception as e:
                _record_call(name, False, time.time() - start)
                raise
        return wrapper
    return decorator


def requires_confirmation(action_description: str):
    """
    Decorator — wraps a tool so it asks for voice/text confirmation before
    executing. Jarvis says what it's about to do and the user must confirm.

    The decorated function receives an extra `confirmed: bool = False` kwarg.
    If False, it returns the confirmation prompt instead of executing.

    Usage:
        @requires_confirmation("send an email to {to}")
        @function_tool
        async def send_email(to: str, subject: str, body: str) -> str:
            ...
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, confirmed: bool = False, **kwargs):
            if not confirmed:
                # Build a readable summary of what's about to happen
                param_summary = ", ".join(
                    [repr(a) for a in args] +
                    [f"{k}={repr(v)}" for k, v in kwargs.items()]
                )
                return (
                    f"⚠️ Sir, main '{fn.__name__}' execute करने वाला हूं:\n"
                    f"  Action: {action_description}\n"
                    f"  Params: {param_summary}\n\n"
                    f"Confirm करने के लिए बोलें 'haan' या 'proceed'। "
                    f"Cancel के लिए 'nahi' बोलें।\n"
                    f"[Note: Call again with confirmed=True to execute]"
                )
            return await fn(*args, **kwargs)
        return wrapper
    return decorator


# ── Tool health check ─────────────────────────────────────────────────────────

async def check_tool_health(tools: list) -> str:
    """
    Smoke-tests that all registered tools are callable and have docstrings.
    Returns a summary report.
    """
    issues = []
    for tool in tools:
        fn = getattr(tool, "_original_func", tool)
        name = getattr(fn, "__name__", str(tool))
        if not callable(fn):
            issues.append(f"  ✗ {name}: not callable")
        elif not fn.__doc__:
            issues.append(f"  ⚠ {name}: missing docstring")
    if issues:
        return "Tool health issues:\n" + "\n".join(issues)
    return f"✅ All {len(tools)} tools passed health check."
