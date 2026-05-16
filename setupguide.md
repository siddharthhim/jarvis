# JARVIS – Voice AI Assistant with 40+ Tools

A modular, voice‑controlled AI assistant built on **LiveKit Agents** and **Google Gemini**, capable of:
- Web search & OSINT (passive dorking, person recon)
- System control (open/close apps, file management, keyboard/mouse)
- Communication (email, WhatsApp desktop)
- Media (YouTube, downloads)
- Document indexing & RAG (PDF, Word, Excel)
- Ambient plan saving, memory, screenshot, screen share
- Autonomous browser automation & tool synthesis

## 🔧 Setup

1. Clone this repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Install Playwright for browser automation: `playwright install`
6. Copy `.env.example` to `.env` and fill in your API keys
7. Run the agent: `python agent.py`

## 📦 Requirements

See `requirements.txt`. Core packages:
- `livekit-agents`
- `google-generativeai`
- `chromadb`, `duckduckgo-search`, `pyautogui`, `pynput`, `browser-use`, etc.

## 🧠 Features

- **Voice Pipeline** (STT → LLM → TTS) with interruption handling
- **Multimodal** Agent (Gemini Live API) optional
- **Tool calling** – 40+ functions for real‑world automation
- **Persistent memory** (ChromaDB)
- **Document search** over your local files
- **Ambient intelligence** – saves plans to Desktop
- **Self‑synthesis** – can generate new tools on the fly

## ⚠️ Security Note

The `SafeController` (keyboard/mouse control) requires a secret token set in `JARVIS_CONTROL_TOKEN` environment variable. Change the default token before production use.

## 📄 License

MIT – use at your own risk. Ensure compliance with local laws when using automation tools.