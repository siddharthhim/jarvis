# Jarvis — Bug & Issue Fixes Changelog

## Files changed / created

| File | Status |
|------|--------|
| `agent.py` | Fixed |
| `jarvis_memory.py` | Fixed |
| `jarvis_browser_agent.py` | Fixed |
| `jarvis_synthesizer.py` | Fixed |
| `jarvis_ambient.py` | Fixed |
| `jarvis_forager.py` | Fixed |
| `jarvis_prompts.py` | **New** (was missing, caused crash) |
| `jarvis_tool_registry.py` | **New** (central registry + rate limiter) |

---

## Bug Fixes

### 1. `agent.py` — Missing imports crashed startup
**Before:** Imported `jarvis_weather`, `Jarvis_window_CTRL`, `Jarvis_file_opner`,
`Jarvis_prompts`, `sentient` — none committed to the repo. App threw
`ModuleNotFoundError` before the LLM even loaded.

**Fix:** All missing modules are now wrapped in `try/except ImportError` with
graceful warnings. Windows-only tools are guarded with `platform.system()` check.
Created `jarvis_prompts.py` stub that was missing entirely.

---

### 2. `agent.py` — `is_connected` called as property instead of method
**Before:** `while ctx.room.is_connected:` — a bound method is always truthy,
so the loop never exited cleanly.

**Fix:** `while ctx.room.is_connected():` — correct method call.

---

### 3. `jarvis_browser_agent.py` — Browser never closed on exceptions
**Before:** `browser.close()` was only in the happy path. Every failed task
leaked a Playwright browser process.

**Fix:** Wrapped in `try/finally` — browser is **always** closed regardless of
success or failure.

---

### 4. `jarvis_browser_agent.py` — LLM initialized at module-import time
**Before:** `_llm = ChatGoogleGenerativeAI(...)` at module top-level crashed
the entire agent if `GOOGLE_API_KEY` was missing.

**Fix:** `_get_llm()` lazy factory — only runs when the tool is actually called.

---

### 5. `jarvis_memory.py` — Memory ID collision on rapid calls
**Before:** `mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}` — two calls within
the same microsecond → ChromaDB `DuplicateIDError`.

**Fix:** `mem_{uuid.uuid4().hex}` — guaranteed unique every time.

---

### 6. `jarvis_synthesizer.py` — Markdown stripping was fragile
**Before:** Only stripped `` ```python `` (lowercase). Gemini often returns
`` ```Python ``, `` ```py ``, or trailing whitespace variants.

**Fix:** `re.sub(r"^```[a-zA-Z]*\s*\n?", ...)` handles all casing/variants.

---

### 7. `jarvis_synthesizer.py` — Generated tools never hot-loaded
**Before:** Synthesized `.py` files were written to disk but never imported.
The user was told "restart to use them."

**Fix:** `_hot_load_tool()` uses `importlib.util.spec_from_file_location` to
import the module immediately after writing. `load_custom_tools()` is called
at agent startup to reload any previously synthesized tools too.

---

### 8. `jarvis_synthesizer.py` — AI-generated code ran without sandboxing
**Before:** Any code Gemini produced was written and would be executed directly
in the main process — a prompt injection could run `os.remove()` etc.

**Fix:** `_is_safe_code()` runs an AST walk before saving. Banned calls:
`eval`, `exec`, `os.remove`, `shutil.rmtree`, `subprocess.*`, etc. Unsafe code
is rejected with a clear message and never written to disk.

---

### 9. `jarvis_synthesizer.py` — LLM initialized at module-import time
Same issue as browser agent.

**Fix:** `_get_llm()` lazy factory.

---

### 10. `jarvis_memory.py` — Transcript log grew unbounded
**Before:** `open(..., "a")` appended forever with no rotation.

**Fix:** `logging.handlers.RotatingFileHandler` — max 5 MB per file, keeps 3
backups.

---

### 11. `jarvis_memory.py` — Credentials could appear in logs
**Before:** If an exception included kwargs, email/password values would be
logged in plaintext.

**Fix:** `_SensitiveFilter` attached to the root logger redacts any log record
whose message contains keys like `password`, `api_key`, `token`, `secret`.

---

### 12. `jarvis_ambient.py` — Hardcoded `notepad.exe` (Windows-only)
**Before:** `subprocess.Popen(["notepad.exe", ...])` crashed on Linux/macOS.

**Fix:** `_open_file_cross_platform()` dispatches to `notepad.exe` / `open -t`
/ `xdg-open` / `gedit` based on `platform.system()`.

---

## Issue Fixes

### 13. No central tool registry
**New file: `jarvis_tool_registry.py`**

Provides:
- `rate_limited(max_calls, window_seconds)` decorator — prevents runaway loops
- `requires_confirmation(action_description)` decorator — gates destructive tools
- `get_tool_stats()` — call counts, error counts, avg latency per tool
- `check_tool_health(tools)` — smoke-tests all tools have docstrings

### 14. No rate limiting on expensive tools
**Fix:** `jarvis_tool_registry.py` `@rate_limited` decorator. Apply to any tool
that calls external APIs or spawns browser processes.

### 15. Memory grew unbounded
**Fix in `jarvis_memory.py`:** Added `forget_memory` and `prune_old_memories`
tools. Call `prune_old_memories(days=30)` manually or hook it into a scheduler.

### 16. Forager had no session-level quota
**Fix in `jarvis_forager.py`:** `_MAX_SEARCHES_PER_SESSION = 30` counter guards
against accidental DuckDuckGo hammering.

---

## How to apply

Replace the corresponding files in your repo root with the fixed versions.
`jarvis_prompts.py` and `jarvis_tool_registry.py` are new files — add them.

The `jarvis_tools_custom/` directory is auto-created by `jarvis_synthesizer.py`
and should be added to `.gitignore` if you don't want synthesized tools committed.
