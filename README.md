<div align="center">

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd6OWF0MjVkYnRsZGNkcHNtdGN0Z2o3MnQ5cGJ6dXRhb3l2NiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ieaUhBIHssPiRLQB3x/giphy.gif" width="400" />

<br><br>

# 🤖 AI Farm Agent

**Autonomous multi-agent system that operates your computer through natural language.**

*You talk. It thinks. It acts. It verifies.*

<br>

<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Claude_API-Anthropic-6B4FBB?style=for-the-badge&logo=anthropic&logoColor=white" />
<img src="https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
<img src="https://img.shields.io/badge/Status-Active_Development-orange?style=for-the-badge" />

<br><br>

[Quick Start](#-quick-start) · [Architecture](#-system-architecture) · [Agents](#-agent-system) · [Interaction Layer](#-interaction-layer) · [Roadmap](#-roadmap) · [Contributing](#-contributing)

</div>

---

<br>

## 🔍 What is AI Farm Agent?

AI Farm Agent transforms natural language commands into real actions on your Windows PC. It doesn't simulate — it **actually opens apps, clicks buttons, types text, creates files, and navigates interfaces** just like a human would.

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   You say:  "Crie uma planilha de vendas Q1-Q4 e abra no Excel"     │
│                                                                      │
│   Agent:    ✅ Generates Python code with openpyxl                   │
│             ✅ Creates formatted .xlsx with headers, borders, data   │
│             ✅ Saves to Desktop                                      │
│             ✅ Opens file in Excel                                   │
│             ✅ Reports success via WebSocket                         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### How does it decide?

<div align="center">

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmRubGhkOWd6ZXl2bm5pNTRpZnRxNHJ0OWR3aWl3eDdzZ3F3aCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/VHrFbmOtBwyMXyNMXn/giphy.gif" width="250" />

<br>

*Like the red pill — once the agent sees the system, there's no going back.*

</div>

<br>

## 🏛 System Architecture

The system uses a **hierarchical multi-agent architecture** where a central orchestrator (Maestro) delegates tasks to specialized agents. Each agent is domain-expert and uses the optimal AI model for its complexity level.

```
                              ┌─────────────┐
                              │   👤 USER    │
                              │  (PT-BR NL)  │
                              └──────┬───────┘
                                     │ WebSocket
                                     ▼
                        ┌────────────────────────┐
                        │      MAESTRO           │
                        │  ┌──────────────────┐  │
                        │  │ Task Analyzer     │  │
                        │  │ Agent Router      │  │
                        │  │ Model: Haiku 4.5  │  │
                        │  └──────────────────┘  │
                        └────────────┬───────────┘
                                     │
          ┌──────────┬───────────────┼───────────────┬──────────┐
          ▼          ▼               ▼               ▼          ▼
   ┌────────┐ ┌──────────┐  ┌────────────┐  ┌──────────┐ ┌────────┐
   │  DATA  │ │   WEB    │  │    CODE    │  │ DESKTOP  │ │  FILE  │
   │ Agent  │ │  Agent   │  │   Agent    │  │  Agent   │ │ Agent  │
   │        │ │          │  │            │  │          │ │        │
   │Haiku4.5│ │ Haiku4.5 │  │ Sonnet 4   │  │ Sonnet 4 │ │Haiku4.5│
   │openpyxl│ │Playwright│  │ subprocess │  │pywinauto │ │os/shutil│
   └────────┘ └──────────┘  └────────────┘  └──────────┘ └────────┘
          │          │               │               │          │
          └──────────┴───────────────┼───────────────┴──────────┘
                                     ▼
                        ┌────────────────────────┐
                        │   INTERACTION LAYER     │
                        │                         │
                        │  L1: API/Code  → 99%    │
                        │  L2: UIA       → 95%    │
                        │  L3: Vision    → 80%    │
                        └────────────┬────────────┘
                                     ▼
                        ┌────────────────────────┐
                        │  SUPPORT SYSTEMS       │
                        │                         │
                        │  👁️ Vision Maestro      │
                        │  🔄 Retry Engine        │
                        │  🧠 Memory Agent        │
                        │  📝 Action Logger       │
                        │  ⏳ Wait Engine         │
                        └────────────────────────┘
```

<br>

## 🤖 Agent System

### Agent Registry

| Agent | Model | Cost | Responsibility | Trigger Examples |
|:------|:------|:-----|:---------------|:----------------|
| **Maestro** | Haiku 4.5 | 💲 | Analyzes task, routes to correct agent | Every task |
| **Vision Maestro** | Haiku 4.5 | 💲 | Validates screen state before/after actions | Visual actions |
| **Data Agent** | Haiku 4.5 | 💲 | Excel, charts, data analysis via openpyxl | *"planilha", "gráfico", "Excel"* |
| **Web Agent** | Haiku 4.5 | 💲 | Browser automation via Playwright | *"pesquise", "abra site", "Google"* |
| **Code Agent** | Sonnet 4 | 💲💲 | Project creation, code generation | *"crie um site", "código", "projeto"* |
| **Desktop Agent** | Sonnet 4 | 💲💲 | App interaction via UIA + Vision | *"Teams", "WhatsApp", "abra o Word"* |
| **File Agent** | Haiku 4.5 | 💲 | File organization via os/shutil | *"organize", "mova", "delete"* |
| **Memory Agent** | Haiku 4.5 | 💲 | Caches successful workflows | Automatic |

### Cost Strategy

Using **Haiku** for routing and simple tasks + **Sonnet** only for complex reasoning achieves **~70% cost reduction** compared to a single-model approach.

```
Haiku 4.5  →  Fast, cheap       →  Routing, data, web, files
Sonnet 4   →  Powerful, precise  →  Code generation, desktop interaction, vision analysis
```

<br>

## ⚡ Interaction Layer

This is the core innovation. Instead of blindly clicking pixels, the system chooses the **most reliable method** for each interaction, cascading through 3 levels:

<div align="center">

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│   LEVEL 1 ━━━ API / Direct Code ━━━ 99% reliable    │
│   │          openpyxl, Playwright, subprocess         │
│   │          Cost: $0  ·  Speed: instant              │
│   │                                                   │
│   │ fallback                                          │
│   ▼                                                   │
│   LEVEL 2 ━━━ UI Automation (UIA) ━━━ 95% reliable   │
│   │          pywinauto accessibility tree              │
│   │          Cost: $0  ·  Speed: fast                 │
│   │                                                   │
│   │ fallback                                          │
│   ▼                                                   │
│   LEVEL 3 ━━━ Vision + PyAutoGUI ━━━ 80% reliable    │
│              Claude Vision + screenshot analysis      │
│              Cost: API tokens  ·  Speed: slow         │
│                                                       │
└───────────────────────────────────────────────────────┘
```

</div>

### When is each level used?

| Scenario | Level | Method |
|:---------|:------|:-------|
| Create/edit spreadsheet | L1 - API | openpyxl generates .xlsx directly |
| Navigate website | L1 - API | Playwright with CSS selectors |
| Click Teams button | L2 - UIA | pywinauto accessibility tree |
| Type in Notepad | L2 - UIA | pywinauto window focus + send text |
| App without UIA support | L3 - Vision | Claude Vision locates + PyAutoGUI clicks |

<br>

## 🔄 Pipeline Flow

```python
# 1. User sends task via WebSocket
"Crie uma planilha de vendas e abra no Excel"

# 2. Memory Agent checks for cached workflow
memory.find_template(task)  # → Found? Skip planning. Not found? Continue.

# 3. Maestro analyzes and routes
maestro.analyze(task)
# → {"agent": "DATA", "subtasks": [{"task": "criar planilha vendas"}]}

# 4. Agent generates execution plan
data_agent.plan(subtask)
# → {"steps": [{"action": "run_python", "code": "import openpyxl..."}]}

# 5. Each step executes through the pipeline
for step in steps:
    state_machine.identify_state(app)      # Where are we?
    interaction_layer.execute(step)         # API → UIA → Vision
    wait_engine.wait_for_condition(...)     # Conditional wait
    retry_engine.handle_failure(...)        # Self-healing if needed
    action_logger.log(step, result)         # JSONL logging
    socketio.emit("step_result", result)    # Real-time UI update

# 6. On success
memory_agent.save_workflow(task, steps)     # Cache for reuse
narrator.generate_report(task, results)     # Skill-builder report
socketio.emit("task_complete")
```

<br>

## 🛡️ Self-Healing — Retry Engine

When a step fails, the system doesn't just retry blindly. It **diagnoses** the failure and picks a recovery strategy:

| Strategy | Trigger | Action |
|:---------|:--------|:-------|
| `WAIT_AND_RETRY` | Element still loading | Wait 2-3s, try again |
| `ALTERNATIVE_PATH` | Popup/dialog blocking | Close popup, retry |
| `RECOVER_STATE` | Wrong window in focus | Alt+Tab, Escape, refocus |
| `ESCALATE_METHOD` | UIA failed | Escalate to Vision (L3) |
| `ABORT` | Unrecoverable error | Stop with detailed log |

<br>

## 🗺️ State Machines

Each supported app has a **navigation map** (JSON) that defines states and transitions. The agent knows where it is and how to get where it needs to be — deterministically, not by guessing.

```json
// state_maps/teams.json (simplified)
{
  "app": "Microsoft Teams",
  "states": {
    "main":      { "transitions": { "chat_list": ["click Chat"] } },
    "chat_list": { "transitions": { "chat_open": ["click {contact}"] } },
    "chat_open": { "transitions": { "message_sent": ["type {msg}", "press Enter"] } }
  }
}
```

**Supported apps:** Teams, Excel, VS Code, Chrome, Explorer — extensible via JSON.

<br>

## 📁 Project Structure

```
ai-farm-agent/
├── main.py                          # Entry point — .env, Flask, browser
├── requirements.txt                 # Dependencies
├── .env                             # API key (git-ignored)
│
├── agents/                          # 🤖 Multi-agent system
│   ├── maestro.py                   # Orchestrator — routes tasks
│   ├── vision_maestro.py            # Visual supervisor
│   ├── data_agent.py                # Excel / data specialist
│   ├── web_agent.py                 # Playwright browser agent
│   ├── code_agent.py                # Code generation (Sonnet)
│   ├── desktop_agent.py             # App interaction (Sonnet)
│   ├── file_agent.py                # File management
│   ├── memory_agent.py              # Workflow caching
│   └── app_routines.py              # Pre-built app routines
│
├── core/                            # ⚙️ Execution engine
│   ├── automation.py                # Action executor
│   ├── interaction_layer.py         # L1 → L2 → L3 cascade
│   ├── uia_driver.py                # pywinauto driver
│   ├── state_machine.py             # JSON-based navigation
│   ├── retry_engine.py              # 5-strategy self-healing
│   ├── wait_engine.py               # Conditional waits
│   ├── ocr_local.py                 # EasyOCR (no API cost)
│   ├── vision.py                    # Claude Vision engine
│   ├── capture.py                   # Screenshot capture
│   ├── action_logger.py             # JSONL structured logging
│   ├── narrator.py                  # Skill-builder reports
│   └── json_validator.py            # Safe JSON parsing
│
├── memory/                          # 🧠 Workflow learning
│   ├── workflow_store.py            # Save/load templates
│   └── workflows/                   # Cached workflows (JSON)
│
├── state_maps/                      # 🗺️ App navigation maps
│   ├── teams.json
│   ├── excel.json
│   ├── vscode.json
│   ├── chrome.json
│   └── explorer.json
│
├── ui/                              # 🖥️ Web interface
│   ├── server.py                    # Flask + SocketIO
│   ├── templates/index.html
│   └── static/{css,js}
│
├── logs/actions.jsonl               # Action logs
├── captures/                        # Screenshots
└── reports/                         # Task reports
```

<br>

## 🚀 Quick Start

<div align="center">

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaGh2Mmp3ZXF0NXdtYmYzN3VwdTluMTdsNnRhdXZnczByaXV6a2ZwcCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/3o7btNhMBytxAM6YBa/giphy.gif" width="350" />

<br>

*Choose your pill. There's no going back.*

</div>

<br>

### Prerequisites

| Requirement | Version |
|:------------|:--------|
| OS | Windows 10/11 (PT-BR recommended) |
| Python | 3.11+ |
| API Key | [Anthropic Console](https://console.anthropic.com/) |

### Installation

```bash
# Clone
git clone https://github.com/ognistie/AI-Farm-Agent.git
cd AI-Farm-Agent/ai-farm-agent

# Virtual environment
python -m venv .venv
.venv\Scripts\activate

# Dependencies
pip install -r requirements.txt
pip install pywinauto easyocr
python -m playwright install chromium

# Configuration
copy .env.example .env
# Edit .env → paste your ANTHROPIC_API_KEY

# Launch
python main.py
```

Web interface opens at `http://127.0.0.1:5000`

### Test Commands

```
📊  "Crie uma planilha com nomes de frutas e preços"
🌐  "Pesquise no Google sobre inteligência artificial"
💻  "Crie um site sobre café com HTML e CSS"
📁  "Organize meus Downloads por tipo de arquivo"
💬  "Mande 'oi' para João no Teams"
```

<br>

## 📊 Available Actions

<details>
<summary><b>📊 Data & Code Execution</b></summary>

```
run_python(code, description)    Execute Python with 18 pre-injected modules
excel_write(data, path)          Create formatted Excel via openpyxl
pip_install(library)             Auto-install packages
```
</details>

<details>
<summary><b>🌐 Web Automation (Playwright)</b></summary>

```
web_goto(url)                    Navigate (auto-opens browser)
web_type(field, text)            Type in form fields
web_click(target)                Click by text/selector
web_key(key)                     Keyboard input
web_read()                       Extract page content
web_new_tab(url)                 Open new tab
web_wait_for(selector, timeout)  Wait for element
```
</details>

<details>
<summary><b>🖥️ Desktop Interaction</b></summary>

```
app_open(name)                   Open application
uia_click(app, element)          Click via accessibility tree (L2)
uia_type(app, field, text)       Type via accessibility tree (L2)
vision_click(description)        AI-guided click (L3)
vision_type(description, text)   AI-guided type (L3)
vision_smart(goal)               AI decides best action
hotkey(keys)                     Keyboard shortcuts
focus_window(title)              Focus window by title
```
</details>

<details>
<summary><b>📁 File Management</b></summary>

```
create_folder(path)              Create directory
write_file(path, content)        Write file
read_file(path)                  Read content
move_file(src, dest)             Move/rename
copy_file(src, dest)             Copy
find_files(path, pattern)        Search by pattern
delete_file(path)                Delete (with safety)
```
</details>

<details>
<summary><b>🔧 System & Navigation</b></summary>

```
wait_for_window(title, timeout)  Conditional window wait
wait_for_element(app, element)   Wait for UI element
navigate_to_state(app, state)    State machine navigation
ocr_read_screen(region)          Local OCR (zero cost)
screenshot()                     Capture screen
```
</details>

<br>

## 🗺️ Roadmap

| Version | Status | Features |
|:--------|:-------|:---------|
| **v1.0** | ✅ Done | Multi-agent, run_python, Vision Maestro, Web UI |
| **v1.5** | 🔧 In Progress | Interaction Layer, UIA, Retry Engine, Logging |
| **v2.0** | 📋 Planned | State Machines, Memory Agent, OCR Local |
| **v2.5** | 📋 Planned | Metrics Dashboard, Automated Tests, CI/CD |
| **v3.0** | 🔮 Future | Full Autonomy — task queues, triggers, scheduling |
| **v4.0** | 🔮 Future | SaaS Platform — multi-user, REST API, installer |

<br>

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| AI Engine | Claude API (Anthropic) | LLM reasoning + computer vision |
| Backend | Flask + SocketIO | Real-time bidirectional communication |
| UI Automation | pywinauto | Windows accessibility tree access |
| Browser | Playwright | Headless web automation |
| GUI Fallback | PyAutoGUI | Mouse/keyboard simulation |
| Vision | Claude Vision + EasyOCR | Screenshot analysis + local OCR |
| Data | openpyxl + pandas | Excel manipulation |
| Frontend | HTML/CSS/JS | WebSocket-powered live dashboard |

<br>

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

```bash
# Quick start for contributors
git clone https://github.com/ognistie/AI-Farm-Agent.git
cd AI-Farm-Agent/ai-farm-agent
pip install -r requirements.txt
copy .env.example .env
# Add your ANTHROPIC_API_KEY to .env
python main.py
```

### Adding a new agent
1. Create `agents/your_agent.py` following existing patterns
2. Register in `ui/server.py`
3. Update `agents/maestro.py` prompt to include the new agent

### Adding support for a new app
1. Map controls: `uia.list_controls("AppName")`
2. Create `state_maps/appname.json` with states & transitions
3. Add controls to `CONTROL_MAPS` in `core/uia_driver.py`
4. Test each transition before integrating

<br>

## ⚠️ Notes

- **Windows only** — Uses Windows-specific APIs (pywinauto, pygetwindow)
- **PT-BR optimized** — UI labels and OCR configured for Brazilian Portuguese
- **API costs** — Vision calls consume tokens; the 3-level cascade minimizes this
- **Security** — Never commit `.env`. Use `.env.example` as template

<br>

---

<div align="center">

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdml5djZ6cnR5anRnbWp2dXJ5dWJyZGV6ZXNxaHdkd2R5Z3R3a3dsaSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/sULKEgDMX8LcI/giphy.gif" width="300" />

<br><br>

**Built by [@ognistie](https://github.com/ognistie)** — Guilherme Moraes Franco

*AI Farm Agent — Teaching computers to operate themselves.*

<br>

<img src="https://img.shields.io/badge/Made_with-Python-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Powered_by-Claude_AI-6B4FBB?style=flat-square&logo=anthropic&logoColor=white" />

</div>
