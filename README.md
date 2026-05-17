<div align="center">

# 🤖 JARVIS

### Autonomous Multimodal AI Assistant

*Perception → Memory → Planning → Action*

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-black?style=for-the-badge)](https://deepmind.google/gemini)
[![LiveKit](https://img.shields.io/badge/LiveKit-Agents-orange?style=for-the-badge)](https://livekit.io)
[![Status](https://img.shields.io/badge/Status-Active_Development-green?style=for-the-badge)](https://github.com/siddharthhim/jarvis)
[![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)](LICENSE)

</div>

---

## What is Jarvis?

Jarvis is not a chatbot. It is an autonomous AI operating assistant that perceives its environment, reasons about tasks, executes real actions, and improves itself over time.

It can hear your voice, control your desktop, browse the web, write and run code, conduct research, send emails, manage files, and now — plan multi-step goals, deploy specialist sub-agents in parallel, and reflect on its own performance to get better after every session.

---

## ✨ Core Features

### 🎙️ Voice AI
Real-time voice conversations with VAD, STT, and TTS. Native audio streaming via LiveKit. Supports natural Hinglish conversation.

### 🧠 Semantic Memory
Long-term vector memory powered by ChromaDB and Sentence Transformers. Jarvis remembers what you tell it across sessions and can semantically recall relevant context.

### 🌐 Autonomous Browser Agent
Full web automation via Playwright and browser-use. Jarvis can navigate sites, click, type, extract data, and complete multi-step web workflows without human input.

### 💻 Desktop & OS Control
Opens apps, manages windows and files, controls keyboard and mouse, reads and writes the clipboard, takes screenshots, and monitors active windows.

### 🔍 Research & Intelligence
Deep web research, Google dorking, breach checking, Arxiv and Scholar exploration, and real-time web search via Tavily.

### 📁 Document Intelligence
Indexes and semantically searches PDFs, DOCX files, and Excel spreadsheets stored locally. Ask questions about your documents in natural language.

### 🔐 Face Recognition Auth
OpenCV-based face detection and recognition with an authentication GUI. Jarvis verifies who it's talking to before allowing sensitive operations.

### 📡 System Monitoring
Live CPU, RAM, battery, and disk diagnostics. Jarvis knows the state of your machine at all times.

### 📧 Communication
Sends emails and WhatsApp messages, controls YouTube playback, and downloads media.

### 🧩 Self-Extending Architecture
Jarvis can write its own tools. When it encounters a task it cannot handle, `jarvis_synthesizer` generates a new Python module, saves it to `jarvis_tools_custom/`, and the tool is hot-loaded automatically on the next startup.

---

## 🆕 Advanced Modules

### 🎯 Goal-Directed Reasoning — `jarvis_planner.py`

Jarvis can now break complex goals into structured execution plans before acting.

```
User: "Research quantum computing and write a PDF summary"

Jarvis:
  Step 1 [web_search]      → Search for recent quantum computing news
  Step 2 [forage_knowledge] → Deep-dive Arxiv and Scholar papers
  Step 3 [store_memory]    → Save key findings to long-term memory
  Step 4 [create_pdf]      → Generate a formatted PDF report
```

Plans persist to `jarvis_plans.json` and survive restarts. You can check progress, pause, or abandon a plan at any time.

**Voice commands:** *"Create a plan to...", "Execute the plan", "What step are we on?", "Abandon the plan"*

---

### 🔁 Self-Improvement Loop — `jarvis_reflector.py`

Every tool call Jarvis makes is logged to `jarvis_action_log.jsonl` with its success/failure status. At any time you can ask Jarvis to reflect — it analyzes its recent behavior, identifies patterns in failures and inefficiencies, and writes concrete behavioral improvement rules to `self_notes.txt`.

On the next startup, those notes are automatically injected into the system prompt. Jarvis gets measurably better the more you use it.

```
jarvis_action_log.jsonl  ←  every tool call logged here automatically
        ↓
reflect_on_performance() ←  Gemini analyzes patterns
        ↓
self_notes.txt           ←  improvement rules saved here
        ↓
agent.py startup         ←  notes injected into system prompt
```

**Voice commands:** *"Reflect on your performance", "What have you learned?", "Show action log", "Clear the log"*

---

### 🤖 Multi-Agent Collaboration — `jarvis_orchestrator.py`

For complex tasks, Jarvis deploys specialist sub-agents in parallel using `asyncio.gather()` and synthesizes their outputs into one coherent answer.

**Available agents:**

| Agent | Specialty |
|---|---|
| `ResearchAgent` | Academic sources, Arxiv, web research |
| `BrowserAgent` | Live web navigation and data extraction |
| `CoderAgent` | Python code, scripts, technical solutions |
| `AnalystAgent` | Synthesis, summarization, report writing |

```
User: "Research LLM memory architectures and write example code"

Jarvis deploys in parallel:
  ├── ResearchAgent  → finds papers on MemGPT, LangMem, etc.
  ├── CoderAgent     → writes a Python memory implementation
  └── AnalystAgent   → synthesizes findings + code into a report

All agents run simultaneously. Results combined into one answer.
```

**Voice commands:** *"Use multiple agents to...", "Research X and write code for Y", "What agents do you have?"*

---

## 🏗️ Architecture

```
Jarvis/
├── Core Voice Pipeline
│   ├── agent.py                  ← Main entry point
│   └── agentmultimodal.py        ← Native audio version
│
├── Intelligence Layer
│   ├── jarvis_planner.py         ← 🆕 Goal-directed reasoning
│   ├── jarvis_reflector.py       ← 🆕 Self-improvement loop
│   ├── jarvis_orchestrator.py    ← 🆕 Multi-agent collaboration
│   └── jarvis_synthesizer.py     ← Self-extending tool creation
│
├── Memory & Knowledge
│   ├── jarvis_memory.py          ← Long-term vector memory (ChromaDB)
│   ├── jarvis_doc_indexer.py     ← Local document intelligence
│   └── jarvis_forager.py         ← Academic research (Arxiv/Scholar)
│
├── Perception & Action
│   ├── jarvis_browser_agent.py   ← Autonomous web browsing
│   ├── keyboard_mouse_CTRL.py    ← Desktop input control
│   ├── jarvis_window_CTRL.py     ← Window & app management
│   ├── jarvis_screenshot.py      ← Screen capture
│   └── jarvis_screenshare.py     ← Active window capture
│
├── Communication
│   ├── jarvis_email.py
│   ├── jarvis_whatsapp.py
│   └── jarvis_youtube.py
│
├── Research & Intelligence
│   ├── Jarvis_google_search.py
│   ├── google_dork.py
│   └── sentient.py               ← Person reconnaissance
│
├── Authentication
│   ├── jarvis_auth_engine.py     ← Face recognition
│   └── jarvis_auth_gui.py
│
├── Utilities
│   ├── jarvis_system_info.py
│   ├── jarvis_clipboard.py
│   ├── jarvis_pdf_creator.py
│   ├── jarvis_ambient.py
│   ├── jarvis_weather.py
│   └── jarvis_toolbox.py
│
└── Plugin Ecosystem
    └── jarvis_tools_custom/      ← Auto-generated tools live here
```

---

## ⚡ Tech Stack

| Category | Technologies |
|---|---|
| AI / LLM | Gemini 2.0 Flash, Gemini 2.5 Flash Native Audio |
| Agent Framework | LiveKit Agents |
| Memory | ChromaDB, Sentence Transformers |
| Browser Automation | Playwright, browser-use, LangChain |
| Desktop Control | PyAutoGUI, Pynput, Win32 APIs |
| Vision & Auth | OpenCV, Haar Cascades, LBPH Face Recognition |
| Research | Tavily API, Arxiv, Google Scholar |
| Utilities | Python AsyncIO, HTTPX, FPDF |
| UI | CustomTkinter, Three.js |

---

## 📦 Installation

**1. Clone the repository**
```bash
git clone https://github.com/siddharthhim/jarvis.git
cd jarvis
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
TAVILY_API_KEY=your_tavily_key
OPENWEATHER_API_KEY=your_openweather_key
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**5. Install Playwright browsers**
```bash
playwright install chromium
```

---

## ▶️ Running Jarvis

**Standard voice agent**
```bash
python agent.py dev
```

**Multimodal native audio version**
```bash
python agentmultimodal.py dev
```

---

## 🔥 Example Sessions

**Multi-step research task**
```
You:    "Research the latest breakthroughs in autonomous AI agents and create a PDF report"

Jarvis: Creates a plan with 4 steps
        Executes: web search → academic research → memory store → PDF generation
        Delivers a formatted report to your desktop
```

**Parallel multi-agent task**
```
You:    "Find the best Python async libraries and write me benchmark code"

Jarvis: Deploys ResearchAgent + CoderAgent + AnalystAgent simultaneously
        ResearchAgent finds asyncio, trio, anyio comparisons
        CoderAgent writes benchmark scripts in parallel
        AnalystAgent synthesizes everything into a final recommendation
        Total time: ~8 seconds instead of sequential ~25 seconds
```

**Self-improvement in action**
```
You:    "Reflect on your performance"

Jarvis: Analyzes last 15 tool calls
        Identifies: 3 failed web searches due to vague queries
        Writes rule: "When searching, I will use specific date ranges and site operators"
        Saves to self_notes.txt → active from next session onward
```

**Desktop automation**
```
You:    "Open VS Code, navigate to my AI project, and run the tests"

Jarvis: Opens VS Code
        Finds the project folder
        Opens the integrated terminal
        Runs pytest
        Reports results back via voice
```

---

## 📁 Auto-Generated Files

These files are created automatically at runtime — do not manually edit them:

| File | Purpose |
|---|---|
| `jarvis_plans.json` | Active and completed goal plans |
| `jarvis_action_log.jsonl` | Tool call history for self-improvement |
| `self_notes.txt` | Jarvis's accumulated behavioral improvement notes |
| `jarvis_transcripts.log` | Full conversation history |
| `jarvis_memory_db/` | ChromaDB vector store |
| `jarvis_tools_custom/` | AI-synthesized tool modules |

---

## 🛡️ Security & Safety

Jarvis is built for personal productivity, education, research, and ethical automation on systems you own and control.

It does not support unauthorized system access, surveillance of others, malicious automation, or illegal activity of any kind.

---

## 🤝 Contributing

Contributions, bug reports, and feature ideas are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a pull request

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Jarvis is an experimental step toward autonomous AI systems that interact with the real digital world.**

*Built by [siddharthhim](https://github.com/siddharthhim)*

</div>
