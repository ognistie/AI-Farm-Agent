<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-00FF41?style=for-the-badge&logo=python&logoColor=00FF41&labelColor=0D0D0D" />
  <img src="https://img.shields.io/badge/Claude_API-Anthropic-00FF41?style=for-the-badge&logo=anthropic&logoColor=00FF41&labelColor=0D0D0D" />
  <img src="https://img.shields.io/badge/Platform-Windows_10%2F11-00FF41?style=for-the-badge&logo=windows&logoColor=00FF41&labelColor=0D0D0D" />
  <img src="https://img.shields.io/badge/Status-Active_Development-00FF41?style=for-the-badge&logoColor=00FF41&labelColor=0D0D0D" />
  <img src="https://img.shields.io/badge/License-MIT-00FF41?style=for-the-badge&labelColor=0D0D0D" />
</p>

<br>

<div align="center">

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     █████╗ ██╗    ███████╗ █████╗ ██████╗ ███╗   ███╗            ║
║    ██╔══██╗██║    ██╔════╝██╔══██╗██╔══██╗████╗ ████║            ║
║    ███████║██║    █████╗  ███████║██████╔╝██╔████╔██║            ║
║    ██╔══██║██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║            ║
║    ██║  ██║██║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║            ║
║    ╚═╝  ╚═╝╚═╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝            ║
║                     A G E N T                                    ║
║                                                                  ║
║          "I know what you're thinking, because right now          ║
║           I'm thinking the same thing... Why not automate?"       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**An autonomous multi-agent system that operates your computer like a human.**<br>
*Natural language in. Real-world actions out.*

<br>

[🚀 Quick Start](#-quick-start) · [🏗️ Architecture](#%EF%B8%8F-architecture) · [🤖 Agents](#-the-agents) · [⚡ Actions](#-available-actions) · [🗺️ Roadmap](#%EF%B8%8F-roadmap) · [🤝 Contributing](#-contributing)

</div>

<br>

---

<br>

## 🔴 What is the Matrix?

> *"The Matrix is everywhere. It is all around us. Even now, in this very room."*

**AI Farm Agent** is a system that sees your computer the way Neo sees the Matrix — not as pixels on a screen, but as a structured world of windows, buttons, text fields, and workflows that can be understood, navigated, and controlled.

You speak in natural language. The system **thinks**, **plans**, **executes**, and **verifies** — operating Excel, Teams, VS Code, browsers, and any Windows application autonomously.

```
You say:   "Create a sales spreadsheet with Q1-Q4 data and open it in Excel"
           "Send 'meeting at 3pm' to João on Teams"
           "Build a portfolio website with HTML/CSS and open in VS Code"

The Agent: Understands → Plans → Executes → Verifies → Reports
```

<br>

## ✨ The Red Pill — Features

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🧠 MULTI-AGENT INTELLIGENCE                               │
│     6 specialized agents orchestrated by a Maestro          │
│                                                             │
│  👁️ COMPUTER VISION                                         │
│     Sees and understands the screen via Claude Vision       │
│                                                             │
│  🎯 3-LEVEL INTERACTION                                     │
│     API → UI Automation → Vision (smart fallback cascade)   │
│                                                             │
│  🔄 SELF-HEALING                                            │
│     Retry engine with 5 recovery strategies                 │
│                                                             │
│  🧭 STATE MACHINES                                          │
│     Deterministic navigation maps for each application      │
│                                                             │
│  🧠 MEMORY                                                  │
│     Learns from successful workflows for instant replay     │
│                                                             │
│  📊 REAL-TIME UI                                            │
│     Live feedback via WebSocket — watch the agent work      │
│                                                             │
│  📝 STRUCTURED LOGGING                                      │
│     Every action logged in JSONL for debugging & analytics  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<br>

## 🏗️ Architecture

> *"There is a difference between knowing the path and walking the path."*

The system follows a clear hierarchy — each agent is a specialist, and the Maestro is the Oracle.

```
                          ┌──────────────┐
                          │   USER       │
                          │  "do X..."   │
                          └──────┬───────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │      🧠 MAESTRO        │
                    │   (The Oracle)         │
                    │   Analyzes → Routes    │
                    └────────────┬───────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
    ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
    │ 👁️ VISION       │ │ 🔄 RETRY     │ │ 🧠 MEMORY       │
    │ MAESTRO         │ │ ENGINE       │ │ AGENT           │
    │ (Supervisor)    │ │ (Self-Heal)  │ │ (Learn/Recall)  │
    └─────────────────┘ └──────────────┘ └─────────────────┘
              │
              ├──────────────────────────────────────────┐
              │                                          │
   ┌──────────┼──────────┬──────────┬──────────┐        │
   ▼          ▼          ▼          ▼          ▼        │
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │
│ DATA │  │ WEB  │  │ CODE │  │DSKTOP│  │ FILE │      │
│Agent │  │Agent │  │Agent │  │Agent │  │Agent │      │
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘      │
   │         │         │         │         │           │
   └─────────┴─────────┴─────────┴─────────┘           │
                       │                                │
                       ▼                                │
          ┌────────────────────────┐                    │
          │  ⚡ INTERACTION LAYER  │◄───────────────────┘
          │                        │
          │  Level 1: API/Code     │  99% reliable
          │  Level 2: UIA          │  95% reliable
          │  Level 3: Vision       │  80% reliable
          └────────────┬───────────┘
                       │
                       ▼
              ┌────────────────┐
              │  🖥️ YOUR PC    │
              │  Windows 10/11 │
              └────────────────┘
```

<br>

## 🤖 The Agents

> *"I can only show you the door. You're the one that has to walk through it."*

Each agent is a senior specialist in its domain. The Maestro routes tasks to the right agent automatically.

| Agent | Codename | Model | Domain | Example |
|-------|----------|-------|--------|---------|
| **Maestro** | The Oracle | `Haiku 4.5` | Task analysis & routing | *"This is a DATA task"* |
| **Vision Maestro** | The Architect | `Haiku 4.5` | Screen supervision | *"Excel is open and ready"* |
| **Data Agent** | The Keymaker | `Haiku 4.5` | Excel, charts, analysis | *"Create sales report"* |
| **Web Agent** | The Merovingian | `Haiku 4.5` | Browser & web navigation | *"Search Google for X"* |
| **Code Agent** | The One | `Sonnet 4` | Programming & projects | *"Build a React website"* |
| **Desktop Agent** | Trinity | `Sonnet 4` | App interaction | *"Send message on Teams"* |
| **File Agent** | Tank | `Haiku 4.5` | File organization | *"Organize my Downloads"* |
| **Memory Agent** | The Operator | `Haiku 4.5` | Workflow memory | *"I've done this before"* |

### 💰 Cost Optimization

The system uses **Haiku** (cheap, fast) for simple routing and **Sonnet** (powerful, precise) only when complexity demands it. This achieves ~70% cost reduction compared to using a single powerful model for everything.

<br>

## ⚡ Available Actions

<details>
<summary><b>📊 Data & Excel</b></summary>

| Action | Description |
|--------|-------------|
| `run_python(code)` | Execute arbitrary Python with 18 pre-injected stdlib modules |
| `excel_write(data, path)` | Create formatted Excel files with openpyxl |
| `pip_install(lib)` | Auto-install Python packages |

</details>

<details>
<summary><b>🌐 Web (Playwright)</b></summary>

| Action | Description |
|--------|-------------|
| `web_goto(url)` | Navigate to URL (auto-opens browser) |
| `web_type(field, text)` | Type in form fields |
| `web_click(target)` | Click elements by text |
| `web_key(key)` | Press keyboard keys |
| `web_read()` | Read page content |
| `web_new_tab(url)` | Open new tab |

</details>

<details>
<summary><b>🖥️ Desktop Apps</b></summary>

| Action | Description |
|--------|-------------|
| `app_open(name)` | Open application |
| `app_interact(app, element, action)` | Interact via UIA → Vision cascade |
| `vision_click(description)` | AI sees screen and clicks |
| `vision_type(description, text)` | AI sees, clicks field, and types |
| `vision_smart(goal)` | AI decides best action |
| `uia_click(app, element)` | Click via accessibility tree |
| `uia_type(app, field, text)` | Type via accessibility tree |
| `hotkey(keys)` | Keyboard shortcuts |

</details>

<details>
<summary><b>📁 Files</b></summary>

| Action | Description |
|--------|-------------|
| `create_folder(path)` | Create directory |
| `write_file(path, content)` | Write file |
| `read_file(path)` | Read file content |
| `move_file(src, dest)` | Move/rename file |
| `find_files(path, pattern)` | Search files by pattern |
| `copy_file(src, dest)` | Copy file |
| `delete_file(path)` | Delete file (with confirmation) |

</details>

<details>
<summary><b>🔧 System</b></summary>

| Action | Description |
|--------|-------------|
| `wait_for_window(title, timeout)` | Conditional wait for window |
| `wait_for_element(app, element)` | Wait for UI element |
| `navigate_to_state(app, state)` | State machine navigation |
| `ocr_read_screen(region)` | Local OCR without API cost |
| `screenshot()` | Capture current screen |

</details>

<br>

## 📁 Project Structure

```
ai-farm-agent/
│
├── main.py                    # ⚡ Entry point — loads .env, starts Flask
├── requirements.txt           # 📦 Dependencies
├── .env                       # 🔑 ANTHROPIC_API_KEY (git-ignored)
│
├── agents/                    # 🤖 Multi-agent system
│   ├── maestro.py             #    The Oracle — task analysis & routing
│   ├── vision_maestro.py      #    The Architect — visual supervision
│   ├── data_agent.py          #    The Keymaker — Excel & data
│   ├── web_agent.py           #    The Merovingian — web navigation
│   ├── code_agent.py          #    The One — programming
│   ├── desktop_agent.py       #    Trinity — app interaction
│   ├── file_agent.py          #    Tank — file management
│   ├── memory_agent.py        #    The Operator — workflow memory
│   └── app_routines.py        #    Pre-built routines (Teams, WhatsApp...)
│
├── core/                      # ⚙️ Execution engine
│   ├── automation.py          #    Action executor
│   ├── interaction_layer.py   #    API → UIA → Vision cascade
│   ├── uia_driver.py          #    Windows UI Automation (pywinauto)
│   ├── state_machine.py       #    Deterministic app navigation
│   ├── retry_engine.py        #    Self-healing with 5 strategies
│   ├── wait_engine.py         #    Conditional waits (no more sleep)
│   ├── ocr_local.py           #    Local OCR with EasyOCR
│   ├── vision.py              #    Claude Vision — screenshot analysis
│   ├── capture.py             #    Screenshot capture
│   ├── action_logger.py       #    Structured JSONL logging
│   ├── narrator.py            #    Skill-builder reports
│   └── json_validator.py      #    Safe JSON parsing
│
├── memory/                    # 🧠 Learning system
│   ├── workflow_store.py      #    Save/load workflow templates
│   └── workflows/             #    Stored successful workflows
│
├── state_maps/                # 🗺️ Application state maps
│   ├── teams.json             #    Microsoft Teams navigation
│   ├── excel.json             #    Excel states
│   ├── vscode.json            #    VS Code states
│   ├── chrome.json            #    Chrome states
│   └── explorer.json          #    File Explorer states
│
├── ui/                        # 🎨 Web interface
│   ├── server.py              #    Flask + SocketIO server
│   ├── templates/index.html   #    Main page
│   └── static/
│       ├── css/style.css      #    Dark glassmorphism theme
│       └── js/app.js          #    WebSocket client
│
├── logs/                      # 📊 Structured logs
│   └── actions.jsonl          #    One JSON line per action
│
├── captures/                  # 📸 Screenshots
└── reports/                   # 📋 Task reports
```

<br>

## 🚀 Quick Start

> *"Free your mind."*

### Prerequisites

- **Windows 10/11** (PT-BR recommended)
- **Python 3.11+**
- **Anthropic API Key** ([get one here](https://console.anthropic.com/))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ognistie/AI-Farm-Agent.git
cd AI-Farm-Agent/ai-farm-agent

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install pywinauto easyocr
python -m playwright install chromium

# 4. Configure your API key
copy .env.example .env
# Edit .env and paste your ANTHROPIC_API_KEY

# 5. Run
python main.py
```

The web interface opens automatically at `http://127.0.0.1:5000`

### First Commands to Try

```
📊  "Crie uma planilha com nomes de frutas e preços"
🌐  "Pesquise no Google sobre inteligência artificial"
💻  "Crie um site sobre café com HTML e CSS"
📁  "Organize meus Downloads por tipo de arquivo"
💬  "Mande 'oi' para João no Teams"
```

<br>

## 🔮 How It Works — The Pipeline

> *"There is no spoon."*

```
1. 💬 User sends task via WebSocket

2. 🧠 Memory Agent: "Have I done this before?"
   → YES: Propose cached workflow (skip planning)
   → NO:  Continue to analysis

3. 🎯 Maestro analyzes task
   → Returns: { agent: "DATA", subtasks: [...] }

4. ⚡ For each subtask:
   a. Agent generates specialized plan → { steps: [...] }
   b. For each step:
      ├─ 🗺️ State Machine identifies current app state
      ├─ 🔀 Interaction Layer picks method: API > UIA > Vision
      ├─ ⏳ Wait Engine: conditional wait (not fixed sleep)
      ├─ 🔄 Retry Engine: manages failures with strategies
      ├─ 📝 Action Logger: records result + timing
      └─ 📡 WebSocket: emits real-time progress

5. ✅ Success?
   → Memory Agent saves workflow as template
   → Narrator generates skill-builder report
   → Emits "task_complete"

6. ❌ Failed?
   → Detailed log of failure point
   → Emits "task_failed" with readable diagnosis
```

<br>

## 🗺️ Roadmap

```
 ✅ v1.0  Multi-agent + run_python + Vision Maestro
 🔧 v1.5  Interaction Layer + UIA + Retry Engine + Logging
 📋 v2.0  State Machines + Memory Agent + OCR Local
 📊 v2.5  Metrics Dashboard + Automated Tests + CI/CD
 🤖 v3.0  Full Autonomy (task queues, triggers, scheduling)
 🌐 v4.0  SaaS Platform (multi-user, REST API, installer)
```

<br>

## 🛡️ Interaction Layer — The Core Innovation

> *"Choice. The problem is choice."*

The system doesn't blindly click pixels. It chooses the most reliable method for each interaction:

```
┌─────────────────────────────────────────────────────────┐
│  LEVEL 1: API / Direct Code          99% reliable       │
│  ─────────────────────────────────────────────────────── │
│  openpyxl creates .xlsx directly, Playwright uses       │
│  CSS selectors, subprocess runs commands.               │
│  Cost: $0 | Speed: Instant                              │
├─────────────────────────────────────────────────────────┤
│  LEVEL 2: UI Automation (UIA)        95% reliable       │
│  ─────────────────────────────────────────────────────── │
│  pywinauto accesses Windows accessibility tree.         │
│  Clicks buttons by name, not by pixel coordinates.      │
│  Cost: $0 | Speed: Fast                                 │
├─────────────────────────────────────────────────────────┤
│  LEVEL 3: Vision + PyAutoGUI         80% reliable       │
│  ─────────────────────────────────────────────────────── │
│  Claude Vision analyzes screenshot, identifies target,  │
│  PyAutoGUI performs the click. Last resort.              │
│  Cost: API tokens | Speed: Slow                         │
└─────────────────────────────────────────────────────────┘
```

<br>

## 🤝 Contributing

> *"Welcome to the real world."*

### Adding a New Agent

```python
# 1. Create agents/new_agent.py following existing patterns
# 2. Register in server.py:
from agents.new_agent import NewAgent
agents["NEW"] = NewAgent()
# 3. Update maestro.py prompt to know about the new agent
```

### Adding Support for a New App

```python
# 1. Open the app and map its controls:
from core.uia_driver import UIADriver
uia = UIADriver()
uia.list_controls("AppName")

# 2. Create state_maps/appname.json with states & transitions
# 3. Add controls to CONTROL_MAPS in uia_driver.py
# 4. Test each transition individually before integrating
```

<br>

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI** | Claude API (Anthropic) | LLM reasoning & vision |
| **Backend** | Flask + SocketIO | Real-time communication |
| **UI Automation** | pywinauto | Windows accessibility tree |
| **Browser** | Playwright | Web automation |
| **GUI Fallback** | PyAutoGUI | Mouse/keyboard simulation |
| **Vision** | Claude Vision + EasyOCR | Screen understanding |
| **Data** | openpyxl | Excel manipulation |
| **Frontend** | HTML/CSS/JS + WebSocket | Live dashboard |

<br>

## ⚠️ Important Notes

- **Windows only** — The system uses Windows-specific APIs (pywinauto, pygetwindow)
- **PT-BR optimized** — UI labels and OCR are configured for Brazilian Portuguese Windows
- **API costs** — Vision calls consume tokens. The 3-level cascade minimizes this
- **Security** — Never commit your `.env` file. Use `.env.example` as template

<br>

---

<br>

<div align="center">

```
"Remember, all I'm offering is the truth. Nothing more."
```

**Built by [@ognistie](https://github.com/ognistie)** · Guilherme Moraes Franco

*AI Farm Agent — Teaching computers to operate themselves.*

<br>

<img src="https://img.shields.io/badge/Made_with-Python-00FF41?style=flat-square&logo=python&logoColor=00FF41&labelColor=0D0D0D" />
<img src="https://img.shields.io/badge/Powered_by-Claude_AI-00FF41?style=flat-square&logo=anthropic&logoColor=00FF41&labelColor=0D0D0D" />
<img src="https://img.shields.io/badge/Inspired_by-The_Matrix-00FF41?style=flat-square&logoColor=00FF41&labelColor=0D0D0D" />

</div>
