<div align="center">

```
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
```

**Autonomous Multimodal AI Assistant**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![LiveKit](https://img.shields.io/badge/LiveKit-Agents_v1.5-black?style=for-the-badge)](https://livekit.io)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange?style=for-the-badge)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active_Dev-brightgreen?style=for-the-badge)]()

*Voice · Memory · Browser · Desktop · Research · Documents · Self-Extending*

</div>

---

## What is Jarvis?

Jarvis is an autonomous AI assistant built in Python that goes far beyond a chatbot. It can hear you, remember you, control your desktop, browse the web autonomously, read your documents, send emails, and even write its own new tools on demand.

It runs on [LiveKit Agents v1.5](https://docs.livekit.io/agents/) and Google Gemini, using a modular architecture where every capability lives in its own file.

```
Perception → Memory → Planning → Action
```

---

## Features

### Voice AI
- Real-time voice conversations via LiveKit WebRTC
- Voice Activity Detection (VAD) with Silero
- Speech-to-Text via Google Cloud (Chirp)
- Text-to-Speech via Google Cloud (Indian English voice)
- Native audio mode via Gemini Live API (`agentmultimodal.py`)
- Hinglish conversational support

### Memory
- Long-term vector memory with ChromaDB
- Semantic search using sentence-transformer embeddings
- Collision-proof UUIDs for every memory entry
- Transcript logging across sessions
- `inject_relevant_memories()` hook for proactive context injection

### Browser Automation
- Autonomous web browsing via `browser-use` + Playwright
- DOM interaction — clicking, typing, form-filling, navigation
- AI-guided task execution with 120s timeout guard
- Browser process always cleaned up (no leaks)

### Desktop & OS Control
- Open and close applications
- File and folder management
- Keyboard and mouse control (PyAutoGUI + Pynput)
- Clipboard read/write
- Screenshots and active-window capture
- Volume control

### Research & Intelligence
- Deep web research via Tavily API
- Google dorking tools
- Scholar and arXiv exploration
- Real-time web search

### Document Intelligence
- PDF, DOCX, XLSX, CSV, TXT indexing
- Incremental re-indexing (unchanged files are skipped)
- Semantic search over your local documents
- Separate vector store from conversation memory

### Communication
- Email automation (Gmail SMTP)
- WhatsApp automation
- YouTube playback control

### Authentication
- Face detection via OpenCV Haar Cascades
- Face recognition via LBPH
- Confidence-threshold authorization check
- Face model stored locally (not committed to git)

### Self-Extending Architecture
- `synthesize_new_tool` — Jarvis writes new Python tools on request
- Generated code is AST-validated and safety-checked before saving
- Custom tools saved to `jarvis_tools_custom/`

---

## Architecture

```
jarvis/
├── agent.py                  ← Main voice agent (STT → LLM → TTS pipeline)
├── agentmultimodal.py        ← Native audio agent (Gemini Live API)
│
├── jarvis_memory.py          ← Long-term vector memory (ChromaDB)
├── jarvis_doc_indexer.py     ← Document indexing & semantic search
├── jarvis_browser_agent.py   ← Autonomous browser (Playwright + browser-use)
├── jarvis_synthesizer.py     ← Self-extending tool generator
│
├── jarvis_screenshot.py      ← Screenshot capture
├── jarvis_screenshare.py     ← Screen + window capture
├── jarvis_clipboard.py       ← Clipboard read/write
├── jarvis_system_info.py     ← CPU, RAM, battery, disk
├── jarvis_ambient.py         ← Ambient task planner
├── jarvis_forager.py         ← Deep knowledge foraging
│
├── keyboard_mouse_CTRL.py    ← Full keyboard + mouse control
├── Jarvis_google_search.py   ← Web search + datetime
├── jarvis_weather.py         ← Weather lookup
├── jarvis_email.py           ← Email automation
├── jarvis_whatsapp.py        ← WhatsApp automation
├── jarvis_youtube.py         ← YouTube control
├── jarvis_toolbox.py         ← Video download utilities
│
├── Jarvis_window_CTRL.py     ← Window / app control
├── Jarvis_file_opner.py      ← File opener
├── jarvis_pdf_creator.py     ← PDF generation
│
├── jarvis_auth_engine.py     ← Face recognition engine
├── jarvis_auth_gui.py        ← Authentication GUI
│
├── google_dork.py            ← Google dorking tools
├── Jarvis_prompts.py         ← System prompt definitions
│
├── jarvis_tools_custom/      ← Auto-generated tools (created at runtime)
├── jarvis_memory_db/         ← ChromaDB: conversation memory
├── jarvis_docs_db/           ← ChromaDB: document knowledge base
└── assets/                   ← Face model data (NOT committed to git)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LiveKit Agents v1.5 |
| LLM | Gemini 2.5 Flash |
| Realtime Audio | Gemini Live API |
| STT | Google Cloud STT (Chirp) |
| TTS | Google Cloud TTS |
| VAD | Silero |
| Vector Memory | ChromaDB + Sentence Transformers |
| Browser Automation | browser-use + Playwright + LangChain |
| Desktop Automation | PyAutoGUI + Pynput + Win32 APIs |
| Face Recognition | OpenCV (LBPH + Haar Cascades) |
| Web Search | Tavily API |
| PDF Generation | FPDF |
| UI | CustomTkinter |

---

## Installation

### 1. Prerequisites

- Python 3.11+
- A [LiveKit Cloud](https://cloud.livekit.io) account (free)
- A [Google AI Studio](https://aistudio.google.com/apikey) API key
- A Google Cloud project with Speech-to-Text API enabled

### 2. Clone the repository

```bash
git clone https://github.com/siddharthhim/jarvis.git
cd jarvis
```

### 3. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

For browser automation, install Playwright browsers:

```bash
playwright install chromium
```

For face recognition, make sure you have `opencv-contrib-python` (not `opencv-python`):

```bash
pip install opencv-contrib-python
```

### 5. Configure environment variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

```env
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Google AI (Gemini)
GOOGLE_API_KEY=your_google_ai_studio_key

# Google Cloud (STT / TTS) — path to service account JSON
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Optional
TAVILY_API_KEY=your_tavily_key
OPENWEATHER_API_KEY=your_openweather_key
EMAIL=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

> **Google Cloud credentials**: Go to Google Cloud Console → IAM & Admin → Service Accounts → Create Key → JSON. Enable the Speech-to-Text API on your project.

---

## Running Jarvis

### Standard voice agent (STT → Gemini LLM → TTS)

```bash
python agent.py console
```

### Multimodal native audio agent (Gemini Live API)

```bash
python agentmultimodal.py console
```

### Connect to LiveKit Agent Console (for browser-based testing)

```bash
python agent.py dev
```

Then open the [Agent Console](https://docs.livekit.io/agents/start/console/) and set agent name to `jarvis`.

---

## Example Interactions

**Voice commands Jarvis understands:**

| What you say | What Jarvis does |
|---|---|
| *"Remember that I prefer dark mode"* | Stores preference in long-term memory |
| *"Open VS Code and start my project"* | Opens app, navigates to folder, runs project |
| *"Search for recent papers on autonomous agents"* | Browses arXiv, summarises findings |
| *"Index my documents"* | Scans Documents folder, builds semantic index |
| *"What did I ask you to remember last week?"* | Recalls relevant memories semantically |
| *"Create a tool that checks disk usage"* | Synthesizes and saves a new Python tool |
| *"Send an email to John about tomorrow's meeting"* | Drafts and sends via Gmail |
| *"Take a screenshot and describe what's on screen"* | Captures screen, analyses with Gemini |

---

## Security & Safety

Jarvis is designed for personal productivity, education, and research on your own machine.

- All desktop automation runs locally
- Face data is stored as a local file and never uploaded
- `assets/` is excluded from git (add to `.gitignore`)
- Synthesized tools are AST-validated before being saved
- Tool synthesis blocks `subprocess`, `socket`, `exec`, `eval`, and other dangerous patterns

Jarvis does **not** support unauthorized access, malicious automation, or illegal activity.

---

## Roadmap

- [ ] Centralized planning engine (decompose multi-step tasks before tool selection)
- [ ] Multi-agent coordination (supervisor + specialist sub-agents)
- [ ] Proactive memory injection before each LLM turn
- [ ] Auto-load synthesized tools without restart
- [ ] Local LLM support (Ollama)
- [ ] Mobile companion app
- [ ] Cloud memory synchronization
- [ ] Task queue for background/ambient jobs

---

## Contributing

Contributions, bug reports, and feature suggestions are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push and open a pull request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

*Jarvis is an experimental step toward autonomous AI systems that can perceive, remember, reason, and act in the real digital world.*

**Built with Python · Powered by Gemini · Runs on LiveKit**

</div>
