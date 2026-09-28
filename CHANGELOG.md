# Changelog

All notable changes to AI Farm Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — 2026-09-23

### Changed
- Replaced the README with implementation-grounded architecture, setup, evaluation and second-brain documentation, including local screenshot assets.
- Adopted the MIT license and aligned contribution terms with open-source use.
- Added security policy and repository review; historical credential exposure and execution-isolation limitations remain documented remediation items.
- Removed generated reports and dated operational journals from version control while preserving local copies; added exclusions for daily journals and legacy learned routes.
- All agents (Maestro, Data, Web, Code, Desktop, File, Vision, Narrator, planner) now run on `claude-sonnet-5`, with per-agent reasoning effort in `config.yaml` (`agent_effort`).
- `AIClient` v3 is now the only path to the API: vision, narrator, VisionMaestro and JSON repair no longer create their own clients. It adds prompt caching on system prompts, streaming, and a cost that includes cache reads and writes. Text is read from `text` blocks only, because Sonnet 5 returns `thinking` blocks first.
- Memory (`workflow_store` v6) stores **routes** (agent sequence, action type, and param names), never content. The Maestro gets these routes as a hint in the prompt and still generates a fresh plan. Entries are upserted per task, failures are recorded, and routes that fail more than they succeed are no longer suggested. Legacy files are moved to `memory/workflows/.legacy/`.
- CodeAgent picks the effort level from task complexity, not the model.

- Desktop UI redesigned:
  - A sidebar with New task, History, About, and recent tasks.
  - A centered composer: Enter sends, Shift+Enter adds a new line, Esc stops a running task.
  - Task runs appear as a live transcript showing the plan, each step's status, the result, links to what was created, and the real cost.
  - The History view reads `history.jsonl` and supports search and reuse of a past task.
  - Removed: the splash screen, metric cards, the Fast/Balanced/Deep buttons (they did nothing), placeholder statistics, and the background glows.
  - Views stay mounted, so a running task is not lost when you switch tabs.
  - Uses the Basic Quick Controls style, the system fonts (Segoe UI Variable, Segoe Fluent Icons), and fractional DPI scaling.

- Second brain in Obsidian (`AI-Farm-agents/`, `core/brain.py`):
  - The vault has a Maestro hub, notes, playbooks and execution rules for each agent, acceptance policies, skills from the AIWorkbench catalog, and reference tasks. It also includes a canvas with the Maestro at the center and graph colors grouped by agent.
  - Agents read their "Regras de execução" section. The Maestro reads similar reference tasks and playbooks as hints.
  - The app writes each validated plan, each agent's proposed steps, and the result (Sucesso/Falhas) to the vault.
- Acceptance policies (`core/plan_validator.py`): the Maestro validates its own plan and each agent's steps before execution, and gets one replan with the literal reason.
- The Maestro now writes requested content (poems, texts, lists) in full. For protected works such as song lyrics it returns `cannot_do` with an alternative instead of writing a substitute. The UI shows this as "limited".

- Subagents (`agents/subagents.py`): each agent has 3 helpers, for understanding the request, assembling the execution input and reviewing it.
  - Web: QueryBuilder, Navigator, ContentGuard
  - Desktop: AppResolver, ContentComposer, ScreenGuard
  - Code: Architect, Builder, Reviewer
  - Data: SchemaDesigner, FormulaChartDesigner, SheetReviewer
  - File: PathResolver, OperationPlanner, SafetyAuditor

  All of them are deterministic except Builder. Their traces go to the log and to the plan note in the vault. A post-step `review_step` hook was added (ContentGuard flags prompt injection in `web_read` output).
- Browser pilot (`core/browser_pilot.py`, action `browser_task`): any browser request beyond "open a known site" or "search on Google/YouTube" is handled by one goal-driven loop, on any site and with no site-specific rules.
  - Each turn it reads the open page through UI Automation (`browser_uia.snapshot`, about 0.3–0.9 s with one batched query).
  - The page is presented in reading order and grouped by region (header, main, sidebars). Text and captioned images sit next to the links they belong to, so prices and "Patrocinado" labels stay with their item, and ads are marked.
  - The model picks one action by element number (click, type, press, goto, scroll, back, vision_click). The pilot runs it and reads the page again.
  - It starts in a new tab, so it never reads or overwrites the tab the user was using. It stops for login, CAPTCHA and irreversible actions it was not asked to do. It rejects cookie banners rather than accepting them, and it refuses to answer from memory before opening a page.
  - A click whose new page title matches the clicked item is marked as confirmed, and going back to re-check is blocked, because result order changes on reload. Repeated actions are detected against the page state, so repeated scrolling is allowed.
  - Tested live on Wikipedia, YouTube, Mercado Livre, Amazon, IBGE, g1, Climatempo, DuckDuckGo, Banco Central and the São Paulo city hall site. Tasks took 1 to 9 turns and cost US$ 0.005–0.03 each; earlier attempts before these fixes cost up to US$ 0.12.
  - `WebAgent` keeps the zero-cost fixed routes only for simple open or search requests (`is_simple_web`). POL-003/POL-007 treat a `browser_task` step as covering search, navigation and clicks. The pilot's action trail is kept out of the text passed to the next subtask.
- Links are now read, not guessed. Without Playwright, `browser_click` uses Windows UI Automation (`core/browser_uia.py`, needs `pywinauto`) to read the real links of the user's own Edge or Chrome (text, URL and position) and clicks through Invoke. It falls back to vision only when no link matches, and then checks that the page title or URL changed; a click with no visible effect now fails.
  - `browser_read` returns the page title, URL, visible text and links, and replaces the `web_read` step that was dropped when Playwright was missing.
  - A Google CAPTCHA page ("unusual traffic") is detected: the step stops with a message and is not retried.
- New `open_path` action (`core/paths.py`): "abra a pasta downloads" or "abrir C:\\projetos" opens the folder directly in one step, with no LLM call. Known folders come from `SHGetKnownFolderPath`, so OneDrive redirection works. Executables and scripts are refused.
- Vision locates elements in two passes: a guess on the downscaled screen, then a crop around it at full resolution. The prompt is generic and has rules for links and result lists. The minimum confidence went from 15% to 50%.
- Second brain now holds 251 reference tasks, 50+ per agent. Each note has context, path, alternative, acceptance criteria, pitfall and the subagents involved. The vault also gets one note per subagent and new Bases panels for references and subagents.

### Fixed
- "Search X and enter site Y" only searched: the query absorbed "e entre no gmail" and the follow-up navigation was never planned. The Web routine now composes three steps: base route, then the requested site, then the requested click.
- "Click the first link in Gmail" opened Gmail and reported success without clicking. Without Playwright, `web_click` was silently dropped. It now becomes a `vision_click`, and "first result" on Google uses the I'm Feeling Lucky URL (`btnI`).
- New policy POL-007: every requested action (enter a site, click) must be in the steps, otherwise the plan is rejected.
- A site requested with "html, css e js" was classified as `static_site`, and the validator then forced removal of the `.js`. An explicit JS request now selects `interactive_site`.
- The FileAgent did not treat imperative delete verbs ("apague", "exclua", "remova", "limpe") as destructive.
- "Open Google and search X" only opened Google: the open-Google routine was checked before search. Search now opens the results URL directly, and Maestro params (`query`, `url`) now reach the agents.
- The WebAgent circuit breaker counted successes, so repeating a search within 5 minutes fell back to the LLM, and the 4th repeat was blocked.
- A task could hang in "Analisando": API calls had no short read timeout, and a cancelled thread stayed alive, emitting events into the next task and clearing its running state. Each run now has a run token.
- The Maestro plan cache used `task[:80]` as its key, so different tasks that started the same way got the same plan.
- The memory shortcut returned only the first agent with empty params, which dropped multi-step subtasks.
- Steps that returned `⚠️`, `⛔` or `Timeout`, and subtasks whose plan failed, were counted as success and saved to memory.
- Execution history stored cumulative session cost per task, which inflated the total cost.
- `MemoryAgent` rejected real tasks that contained the word "teste".
- The static-site prompt had a fixed palette and font, and the Data agent had a fixed header color. Both are now derived from the task theme.

---

## [1.0.0] — 2025

### Added
- Multi-agent architecture with Maestro orchestrator
- 6 specialized agents: Data, Web, Code, Desktop, File, Memory
- Vision Maestro for screen supervision (before/after validation)
- App Routines for Teams, WhatsApp, Notepad, Word, Excel, VS Code, Outlook, Spotify
- Claude Vision integration for screen understanding
- Flask + SocketIO web interface with real-time feedback
- Narrator for skill-builder reports
- Safe JSON parsing with automatic repair
- Screenshot capture with annotations

### Architecture
- Haiku 4.5 for routing/simple tasks, Sonnet 4 for complex reasoning
- ~70% cost reduction vs single-model approach

---

## [Unreleased — v1.5]

### Planned
- Interaction Layer (API → UIA → Vision cascade)
- UIA Driver with pywinauto integration
- Wait Engine (conditional waits replacing fixed sleep)
- Retry Engine with 5 recovery strategies
- Action Logger with JSONL structured logging
- State Machine with JSON navigation maps
- OCR Local with EasyOCR (zero API cost)
