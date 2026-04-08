<!-- ╔══════════════════════════════════════════════════════════════╗ -->
<!-- ║              AI FARM AGENT — README                        ║ -->
<!-- ║              github.com/ognistie/AI-Farm-Agent              ║ -->
<!-- ╚══════════════════════════════════════════════════════════════╝ -->

<div align="center">

<!-- MATRIX RAIN HEADER -->
<img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd6OWF0MjVkYnRsZGNkcHNtdGN0Z2o3MnQ5cGJ6dXRhb3l2NiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ieaUhBIHssPiRLQB3x/giphy.gif" width="100%" />

<br>

<!-- ASCII LOGO -->
```
     █████╗ ██╗    ███████╗ █████╗ ██████╗ ███╗   ███╗
    ██╔══██╗██║    ██╔════╝██╔══██╗██╔══██╗████╗ ████║
    ███████║██║    █████╗  ███████║██████╔╝██╔████╔██║
    ██╔══██║██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║
    ██║  ██║██║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║
    ╚═╝  ╚═╝╚═╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
                    A  G  E  N  T       v1.0
```

<h3>🟢 An autonomous multi-agent system that operates your computer.</h3>
<p><i>Natural language in → Real-world actions out.</i></p>

<br>

<!-- BADGES -->
<a href="#-quick-start"><img src="https://img.shields.io/badge/⚡_QUICK_START-00FF41?style=for-the-badge&labelColor=000000" /></a>
<a href="#-architecture"><img src="https://img.shields.io/badge/🏛_ARCHITECTURE-00FF41?style=for-the-badge&labelColor=000000" /></a>
<a href="#-agents"><img src="https://img.shields.io/badge/🤖_AGENTS-00FF41?style=for-the-badge&labelColor=000000" /></a>
<a href="#-roadmap"><img src="https://img.shields.io/badge/🗺️_ROADMAP-00FF41?style=for-the-badge&labelColor=000000" /></a>

<br><br>

<img src="https://img.shields.io/badge/Python-3.11+-00FF41?style=flat-square&logo=python&logoColor=00FF41&labelColor=0a0a0a" />
<img src="https://img.shields.io/badge/Claude_API-Anthropic-00FF41?style=flat-square&logo=anthropic&logoColor=00FF41&labelColor=0a0a0a" />
<img src="https://img.shields.io/badge/Windows-10%2F11-00FF41?style=flat-square&logo=windows&logoColor=00FF41&labelColor=0a0a0a" />
<img src="https://img.shields.io/badge/MIT-License-00FF41?style=flat-square&labelColor=0a0a0a" />

</div>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🟢 What is this?

> **AI Farm Agent** sees your computer not as pixels — but as a structured world of windows, buttons, fields, and workflows that can be understood and controlled.

You speak naturally. The system **thinks**, **plans**, **executes**, and **verifies** — creating spreadsheets in Excel, sending messages on Teams, building websites in VS Code, organizing files, and navigating the web. Autonomously.

```
 ╭──────────────────────────────────────────────────────────────╮
 │                                                              │
 │  💬 "Crie uma planilha de vendas Q1-Q4 e abra no Excel"     │
 │                                                              │
 │      ┌─────────────────────────────────────────────┐         │
 │      │ 1. 🧠 Maestro routes → DATA AGENT           │         │
 │      │ 2. 📊 Data Agent generates openpyxl code     │         │
 │      │ 3. ⚡ Execution engine runs Python            │         │
 │      │ 4. 📂 .xlsx saved to Desktop                 │         │
 │      │ 5. 🖥️  Excel opens with formatted data       │         │
 │      │ 6. 👁️ Vision Maestro confirms success        │         │
 │      │ 7. ✅ "task_complete" → WebSocket             │         │
 │      └─────────────────────────────────────────────┘         │
 │                                                              │
 │  ⏱ ~4s  ·  💰 ~$0.002  ·  🎯 Method: L1 (API direct)       │
 │                                                              │
 ╰──────────────────────────────────────────────────────────────╯
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🏛 Architecture

<div align="center">



</div>

<br>

```
                              USER
                           "do X..."
                               │
                               ▼
                 ╔═══════════════════════════╗
                 ║        🧠 MAESTRO         ║
                 ║    Haiku 4.5 · ~$0.001    ║
                 ║    Analyze → Decompose    ║
                 ║    → Route to Agent       ║
                 ╚═════════════╤═════════════╝
                               │
         ┌─────────┬───────────┼───────────┬─────────┐
         ▼         ▼           ▼           ▼         ▼
     ┌───────┐ ┌───────┐ ┌─────────┐ ┌────────┐ ┌───────┐
     │  📊   │ │  🌐   │ │   💻    │ │  🖥️    │ │  📁   │
     │ DATA  │ │  WEB  │ │  CODE   │ │DESKTOP │ │ FILE  │
     │       │ │       │ │         │ │        │ │       │
     │Haiku  │ │Haiku  │ │Sonnet 4 │ │Sonnet 4│ │Haiku  │
     │$0.001 │ │$0.001 │ │ $0.01   │ │ $0.01  │ │$0.001 │
     └───┬───┘ └───┬───┘ └────┬────┘ └───┬────┘ └───┬───┘
         └─────────┴──────────┼──────────┴─────────┘
                              ▼
                ╔══════════════════════════╗
                ║  ⚡ INTERACTION LAYER    ║
                ║                          ║
                ║  L1 ██████████████ 99%   ║ ← API/Code
                ║  L2 ████████████░░ 95%   ║ ← UIA
                ║  L3 ████████░░░░░░ 80%   ║ ← Vision
                ╚═════════════╤════════════╝
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
          ┌──────────┐ ┌──────────┐ ┌──────────┐
          │ 👁️ VISION│ │ 🔄 RETRY │ │ 🧠MEMORY │
          │ MAESTRO  │ │  ENGINE  │ │  AGENT   │
          │ validate │ │ 5 strats │ │  cache   │
          └──────────┘ └──────────┘ └──────────┘
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🤖 Agents

### The Team

<table>
<tr>
<td width="50%" valign="top">

#### 🧠 Maestro — _The Brain_
> Routes every task to the right specialist. Analyzes intent, decomposes complex requests into subtasks, and coordinates execution order.
>
> **Model:** `Haiku 4.5` · **Cost:** ~$0.001/call

#### 📊 Data Agent — _The Analyst_
> Creates Excel spreadsheets, charts, and data analysis using `openpyxl`. Generates complete Python code that runs on first attempt.
>
> **Model:** `Haiku 4.5` · **Trigger:** _planilha, dados, Excel_

#### 🌐 Web Agent — _The Navigator_
> Browses the web using `Playwright`. Handles cookies, popups, form submissions, and complex navigation sequences.
>
> **Model:** `Haiku 4.5` · **Trigger:** _pesquise, site, Google_

#### 📁 File Agent — _The Organizer_
> Manages files and folders using `os`/`shutil`. Organizes downloads, moves files, creates directory structures.
>
> **Model:** `Haiku 4.5` · **Trigger:** _organize, mova, copie_

</td>
<td width="50%" valign="top">

#### 💻 Code Agent — _The Builder_
> Creates full projects with HTML, CSS, JS, Python. Generates production-quality code with proper structure and separation.
>
> **Model:** `Sonnet 4` · **Cost:** ~$0.01/call

#### 🖥️ Desktop Agent — _The Operator_
> Interacts with any Windows app via UIA + Vision cascade. Has pre-built routines for Teams, WhatsApp, Word, Outlook, Spotify.
>
> **Model:** `Sonnet 4` · **Trigger:** _Teams, WhatsApp, abra_

#### 👁️ Vision Maestro — _The Watchdog_
> Captures and analyzes screenshots before/after every visual action. Detects errors, popups, wrong windows, and loading states.
>
> **Model:** `Haiku 4.5` · **Scope:** visual actions only

#### 🧠 Memory Agent — _The Archive_
> Caches successful workflows as JSON templates. Next time a similar task appears, it skips planning entirely.
>
> **Model:** — · **Scope:** automatic

</td>
</tr>
</table>

### 💰 Why Two Models?

```
 ┌──────────────────────────────────────────────────────────┐
 │                                                          │
 │  HAIKU 4.5  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  80%      │
 │  Fast · Cheap · Routing, data, web, files                │
 │                                                          │
 │  SONNET 4   ━━━━━━━━━━━━  20%                           │
 │  Powerful · Precise · Code, desktop, vision, retry       │
 │                                                          │
 │  Result: ~70% cost reduction vs single-model approach    │
 │                                                          │
 └──────────────────────────────────────────────────────────┘
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## ⚡ Interaction Layer

**The core innovation.** The system cascades through 3 reliability levels — only falling to the next when the current one fails:

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                                                              ║
 ║  🟢 LEVEL 1 ─── API / Direct Code ──── 99% reliable         ║
 ║  │                                                           ║
 ║  │  openpyxl creates .xlsx directly                          ║
 ║  │  Playwright navigates with selectors                      ║
 ║  │  subprocess runs commands                                 ║
 ║  │  Cost: $0 · Speed: <1s                                    ║
 ║  │                                                           ║
 ║  │  ↓ if not possible                                        ║
 ║  │                                                           ║
 ║  🟡 LEVEL 2 ─── UI Automation (UIA) ── 95% reliable         ║
 ║  │                                                           ║
 ║  │  pywinauto reads Windows accessibility tree               ║
 ║  │  Clicks buttons by name, not coordinates                  ║
 ║  │  No screenshots needed                                    ║
 ║  │  Cost: $0 · Speed: ~2s                                    ║
 ║  │                                                           ║
 ║  │  ↓ if UIA fails                                           ║
 ║  │                                                           ║
 ║  🔴 LEVEL 3 ─── Vision + PyAutoGUI ─── 80% reliable         ║
 ║                                                              ║
 ║     Claude Vision analyzes screenshot                        ║
 ║     Identifies target element coordinates                    ║
 ║     PyAutoGUI performs the click                              ║
 ║     Cost: ~$0.01 · Speed: ~5s                                ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🔄 Pipeline

```python
# ── 1. User sends task via WebSocket ──────────────────────────
task = "Crie uma planilha de vendas e abra no Excel"

# ── 2. Memory check ──────────────────────────────────────────
cached = memory_agent.find_template(task)
if cached: skip_to_execution(cached)

# ── 3. Maestro analyzes ──────────────────────────────────────
plan = maestro.analyze(task)
# → {"agent": "DATA", "subtasks": [...]}

# ── 4. Agent generates steps ─────────────────────────────────
steps = data_agent.plan(subtask)
# → {"steps": [{"action": "run_python", "code": "..."}]}

# ── 5. Execute with full pipeline ────────────────────────────
for step in steps:
    state   = state_machine.identify(app)        # Where are we?
    result  = interaction_layer.execute(step)     # L1 → L2 → L3
    wait    = wait_engine.until(condition)        # Smart wait
    recover = retry_engine.on_failure(result)     # Self-heal
    log     = action_logger.record(step, result)  # JSONL
    emit    = socketio.emit("progress", result)   # Real-time UI

# ── 6. Success ───────────────────────────────────────────────
memory_agent.save(task, steps)                    # Cache workflow
narrator.report(task, results)                    # Generate report
socketio.emit("task_complete")                    # ✅ Done
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🛡️ Self-Healing

When a step fails, the **Retry Engine** diagnoses the problem and chooses a recovery strategy:

```
 FAILURE DETECTED
       │
       ▼
 ┌─────────────────────────────────────────────────────────┐
 │  🔍 DIAGNOSE                                            │
 │                                                         │
 │  "not found" / "timeout"                                │
 │    → WAIT_AND_RETRY (wait 3s, try again)               │
 │                                                         │
 │  "blocked" / "popup" / "dialog"                         │
 │    → ALTERNATIVE_PATH (close blocker, retry)            │
 │                                                         │
 │  "wrong window" / "lost focus"                          │
 │    → RECOVER_STATE (Alt+Tab, Escape, refocus)           │
 │                                                         │
 │  UIA method failed                                      │
 │    → ESCALATE_METHOD (switch to Vision L3)              │
 │                                                         │
 │  "crash" / "permission denied"                          │
 │    → ABORT (stop + detailed error log)                  │
 │                                                         │
 └─────────────────────────────────────────────────────────┘
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🗺️ State Machines

Each supported app has a **JSON navigation map** — the agent always knows where it is and how to reach the target state:

```json
{
  "app": "Microsoft Teams",
  "states": {
    "main":      { "indicators": ["Chat", "Teams", "Calendar"],
                   "transitions": { "chat_list": [{"action": "uia_click", "target": "Chat"}] }},
    "chat_list": { "indicators": ["Recent", "Filter"],
                   "transitions": { "chat_open": [{"action": "uia_click", "target": "{contact}"}] }},
    "chat_open": { "indicators": ["Type a new message"],
                   "transitions": { "sent": [{"action": "uia_type", "text": "{msg}"}, 
                                              {"action": "hotkey", "keys": "Enter"}] }}
  }
}
```

**Supported:** `Teams` · `Excel` · `VS Code` · `Chrome` · `Explorer` — extensible via JSON.

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 📁 Structure

```
ai-farm-agent/
│
├── main.py                        ← Entry point
├── requirements.txt               ← Dependencies
├── .env                           ← API key (git-ignored)
│
├── agents/                        ← 🤖 Multi-agent system
│   ├── maestro.py                    Orchestrator
│   ├── vision_maestro.py             Visual supervisor
│   ├── data_agent.py                 Excel specialist
│   ├── web_agent.py                  Browser specialist
│   ├── code_agent.py                 Code generator
│   ├── desktop_agent.py              App controller
│   ├── file_agent.py                 File manager
│   ├── memory_agent.py               Workflow cache
│   └── app_routines.py               Pre-built routines
│
├── core/                          ← ⚙️ Engine
│   ├── automation.py                 Action executor
│   ├── interaction_layer.py          L1 → L2 → L3 cascade
│   ├── uia_driver.py                 pywinauto driver
│   ├── state_machine.py              JSON navigation
│   ├── retry_engine.py               Self-healing (5 strategies)
│   ├── wait_engine.py                Conditional waits
│   ├── ocr_local.py                  EasyOCR (no API cost)
│   ├── vision.py                     Claude Vision
│   ├── capture.py                    Screenshots
│   ├── action_logger.py              JSONL logging
│   └── json_validator.py             Safe JSON parsing
│
├── memory/                        ← 🧠 Learning
│   ├── workflow_store.py             Template storage
│   └── workflows/                    Cached workflows
│
├── state_maps/                    ← 🗺️ App maps
│   ├── teams.json                    
│   ├── excel.json                    
│   ├── vscode.json                   
│   ├── chrome.json                   
│   └── explorer.json                 
│
├── ui/                            ← 🖥️ Interface
│   ├── server.py                     Flask + SocketIO
│   ├── templates/index.html          
│   └── static/{css,js}/              
│
├── logs/actions.jsonl             ← 📊 Action logs
├── captures/                      ← 📸 Screenshots
└── reports/                       ← 📋 Reports
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🚀 Quick Start

<div align="center">

<img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd6OWF0MjVkYnRsZGNkcHNtdGN0Z2o3MnQ5cGJ6dXRhb3l2NiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ieaUhBIHssPiRLQB3x/giphy.gif" width="100%" />


<br>

_Take the red pill._

</div>

<br>

### Requirements

```
OS          Windows 10/11 (PT-BR recommended)
Python      3.11+
API Key     https://console.anthropic.com/
```

### Install

```bash
# Clone
git clone https://github.com/ognistie/AI-Farm-Agent.git
cd AI-Farm-Agent/ai-farm-agent

# Environment
python -m venv .venv
.venv\Scripts\activate

# Dependencies
pip install -r requirements.txt
pip install pywinauto easyocr
python -m playwright install chromium

# API Key
copy .env.example .env
# → Edit .env with your ANTHROPIC_API_KEY

# Launch
python main.py
```

### Try It

```
📊  "Crie uma planilha com nomes de frutas e preços"
🌐  "Pesquise no Google sobre inteligência artificial"
💻  "Crie um site sobre café com HTML e CSS"
📁  "Organize meus Downloads por tipo de arquivo"
💬  "Mande 'oi' para João no Teams"
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 📊 Available Actions

<details>
<summary>📊 <b>Data & Code</b></summary>
<br>

```
run_python(code)                   Execute Python (18 stdlib modules pre-loaded)
excel_write(data, path)            Create formatted .xlsx via openpyxl
pip_install(lib)                   Auto-install Python packages
```
</details>

<details>
<summary>🌐 <b>Web (Playwright)</b></summary>
<br>

```
web_goto(url)                      Navigate (auto-opens browser)
web_type(field, text)              Type in form fields
web_click(target)                  Click by text/selector
web_key(key)                       Press keyboard key
web_read()                         Extract page text
web_new_tab(url)                   Open new tab
web_wait_for(selector, timeout)    Wait for element
```
</details>

<details>
<summary>🖥️ <b>Desktop</b></summary>
<br>

```
app_open(name)                     Open application
uia_click(app, element)            Click via accessibility tree [L2]
uia_type(app, field, text)         Type via accessibility tree [L2]
vision_click(description)          AI-guided click [L3]
vision_type(description, text)     AI-guided type [L3]
vision_smart(goal)                 AI decides best action [L3]
hotkey(keys)                       Keyboard shortcut
focus_window(title)                Focus window by title
```
</details>

<details>
<summary>📁 <b>Files</b></summary>
<br>

```
create_folder(path)                Create directory
write_file(path, content)          Write file
read_file(path)                    Read content
move_file(src, dest)               Move/rename
copy_file(src, dest)               Copy
find_files(path, pattern)          Search by pattern
delete_file(path)                  Delete (with safety check)
```
</details>

<details>
<summary>🔧 <b>System</b></summary>
<br>

```
wait_for_window(title, timeout)    Wait until window appears
wait_for_element(app, element)     Wait until UI element exists
navigate_to_state(app, state)      State machine navigation
ocr_read_screen(region)            Local OCR (zero API cost)
screenshot()                       Capture current screen
```
</details>

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🛠️ Tech Stack

```
 LAYER             TECHNOLOGY              PURPOSE
 ─────────────────────────────────────────────────────────
 AI Engine         Claude API (Anthropic)   LLM reasoning + vision
 Backend           Flask + SocketIO         Real-time communication
 UI Automation     pywinauto                Windows accessibility tree
 Browser           Playwright               Web automation
 GUI Fallback      PyAutoGUI                Mouse/keyboard simulation
 Vision            Claude Vision + EasyOCR  Screen analysis + local OCR
 Data              openpyxl                 Excel manipulation
 Frontend          HTML/CSS/JS + WS         Live dashboard
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🗺️ Roadmap

```
 VERSION    STATUS              FEATURES
 ──────────────────────────────────────────────────────────────────
 v1.0       ████████████████    Multi-agent, run_python, Vision
            ✅ DONE              Maestro, Web UI, App Routines

 v1.5       ████████░░░░░░░░    Interaction Layer, UIA Driver,
            🔧 IN PROGRESS       Retry Engine, Wait Engine, Logging

 v2.0       ░░░░░░░░░░░░░░░░    State Machines, Memory Agent,
            📋 PLANNED            OCR Local, Workflow Templates

 v2.5       ░░░░░░░░░░░░░░░░    Metrics Dashboard, Tests, CI/CD
            📋 PLANNED

 v3.0       ░░░░░░░░░░░░░░░░    Full Autonomy — queues, triggers
            🔮 FUTURE

 v4.0       ░░░░░░░░░░░░░░░░    SaaS — multi-user, REST API,
            🔮 FUTURE             installer, cloud dashboard
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

## 🤝 Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

```bash
# Fork → Clone → Branch → Code → PR
git clone https://github.com/YOUR_USER/AI-Farm-Agent.git
cd AI-Farm-Agent/ai-farm-agent
pip install -r requirements.txt
copy .env.example .env
python main.py
```

**Add a new agent:** Create `agents/new.py` → Register in `server.py` → Update `maestro.py` prompt

**Add a new app:** Run `uia.list_controls("App")` → Create `state_maps/app.json` → Add to `uia_driver.py`

<br>

## ⚠️ Notes

```
 ⚠ Windows only      Uses pywinauto, pygetwindow (Windows APIs)
 ⚠ PT-BR optimized   UI labels and OCR tuned for Brazilian Portuguese
 ⚠ API costs          Vision (L3) consumes tokens — cascade minimizes this
 ⚠ Security           Never commit .env — use .env.example as template
```

<br>

<!-- GREEN LINE SEPARATOR -->
<img src="https://i.imgur.com/waxVImv.png" width="100%" />

<br>

<div align="center">

<!-- FOOTER GIF -->
<img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd6OWF0MjVkYnRsZGNkcHNtdGN0Z2o3MnQ5cGJ6dXRhb3l2NiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ieaUhBIHssPiRLQB3x/giphy.gif" width="100%" />

<br>

```
 ╔══════════════════════════════════════════════════════════╗
 ║                                                          ║
 ║   Built by @ognistie — Guilherme Moraes Franco           ║
 ║                                                          ║
 ║   "Teaching computers to operate themselves."            ║
 ║                                                          ║
 ╚══════════════════════════════════════════════════════════╝
```

<br>

<img src="https://img.shields.io/badge/MADE_WITH-PYTHON-00FF41?style=for-the-badge&logo=python&logoColor=00FF41&labelColor=000" />
<img src="https://img.shields.io/badge/POWERED_BY-CLAUDE_AI-00FF41?style=for-the-badge&logo=anthropic&logoColor=00FF41&labelColor=000" />
<img src="https://img.shields.io/badge/INSPIRED_BY-THE_MATRIX-00FF41?style=for-the-badge&labelColor=000" />

<br><br>

⬡

</div>