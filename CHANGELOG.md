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
- Continuous conversation: a request can continue the previous one ("open YouTube" → "now open that second video"; "open Notepad" → "now write a text"; "make a site" → "change the main color" → "undo").
  - `core/session.py` keeps the turns of the conversation and what was left open: the browser tab (window, URL, visible items), app windows, the code project and the last folder. It also tracks which of these is in focus.
  - `core/followup.py` turns a follow-up utterance into a complete request with a target. Cancel, undo, answers to a pending question, and self-contained requests are handled without an LLM call; references use one short call to the `resolver` model (low effort). A target the model invents is discarded.
  - `core/observer.py` records what is open after each subtask. The Maestro receives the conversation and a `CONTINUAR EM` target, and the controller passes that target to the matching agent as `params.continue`.
  - In continue mode each agent works on what is already open:
    - Web: the pilot resumes the same tab and checks that it still shows the same page.
    - Desktop: focuses the same window by handle and refuses to type if the active tab or document changed.
    - Code: `CodeAgent.plan_edit` returns only the changed files. A new `edit_project` action saves the previous version to `<project>/.ai_versions/`, and `revert_project` restores it ("desfaz").
  - Answering a clarification question continues the original request and its target instead of starting over.
  - The UI shows the conversation: earlier requests stay above in compact form, each request shows "Entendi: …", and "Nova tarefa" became "Nova conversa".
- Security hardening before the round 4 commit (negative tests in `test_security_guards_round4`):
  - `open_path` refuses network paths (`\\server\share`, `//host/x`, `file:`) before touching them. Merely checking such a path makes Windows authenticate to the remote host and send the NTLM hash.
  - The list of blocked executable types now includes `.msc`, `.jar`, `.url`, `.chm`, `.appinstaller`, `.settingcontent-ms`, disk images, `.dll` and others that run code when opened.
  - The Start-menu fallback of `app_search` (type + Enter) refuses names with paths, arguments (`cmd /c`, `-Command`) or shell symbols. Known apps still open by their fixed program.
  - The voice understanding and conversation resolver prompts now state that page and window text in the context is data, never instructions.
- Voice assistant, round 4: closer to a high-end assistant, with faster and more precise understanding:
  - Instant answers without the model:
    - Local answers for time and date.
    - "abre o X" and "pesquisa X no Google/YouTube" when the speech was heard clearly.
    - A cut-off request ("abre o...") asks what is missing instead of becoming "abrir algum aplicativo".
    - Fillers ("hum") are ignored.
    - About 20% of utterances skip the model.
  - The understanding step now:
    - returns the target the request continues in (Excel, a browser tab, a folder);
    - lets voice commands skip the second resolver call (`followup.from_hint`, validated in code with the same rules);
    - answers knowledge questions directly as `answer`, while live data (prices, weather, news) still goes to the PC;
    - treats comments ("meu time ganhou") as chat, which may *offer* an action but never runs one;
    - treats background talk as noise in live mode;
    - lets accepting an offer ("Quer que eu toque o primeiro?" → "pode") run that offer, because the assistant's replies are now in the conversation context.
  - Persona (`core/voice/persona.py`, editable in Obsidian at `00 Maestro/Persona do assistente`):
    - one speaking style shared by voice understanding, end-of-task replies and small talk;
    - ready-made lines that vary and never repeat the last ones;
    - consequential actions are announced as "prepare and confirm", never as already done.
  - Long tasks get one spoken progress update ("Ainda tô nisso no navegador").
  - The hotkey cuts the assistant's speech in live mode.
  - The queue message says which request is waiting.
- Voice dictionary fixes and expansion (`70 Dicionario/`):
  - Auto-correction was rewriting normal speech: "ponto" became punctuation, "print" gained "(captura de tela)", "vê esse código" became VS Code, and "time" could become Teams. Confusions now carry a `Corrigir` column: only `auto` rows are replaced before understanding, while `dica` rows go to the model as hints.
  - Dictionary excerpts are ranked by specificity, so the most specific matches go first.
  - Sound-alike app detection ("espotifaim" ~ Spotify) is used as a hint only.
  - Expanded from about 1,160 to about 2,630 ways of speaking, in 822 rows.
  - "Apps e sites" gains an "Abrir com" column (URL or program), and "Formas de pedir" now maps intent → how to execute → whether to confirm.
  - New notes: "Configuracoes do Windows" (62 `ms-settings:` pages, used by the Desktop agent beyond the built-in list), "Atalhos de teclado" and "Referencias e contexto".
- The Obsidian vault is now the retrieval source for every agent (`Brain.context_for`):
  - Each LLM-planned step of the Data, Web, Code, Desktop and File agents receives the agent's rules and known failures, matching playbooks and executions, matching lessons learned, and dictionary terms for that request. The browser and app pilots get the same context, and the Maestro also receives matching lessons.
  - Notes consulted are recorded in the plan note ("Consultou: …").
  - Recorded executions rank below curated playbooks, so an automatic "success" cannot outrank a reviewed path.
  - The Desktop agent note and the Word/Excel and Notepad playbooks were updated to match the current behaviour, since agents now read them.
- `scripts/eval_voice.py`: 50 hard utterances (misheard names, slang, stutters, self-correction, background talk, questions, follow-ups) run through the real understanding step without executing anything:
  - Baseline: 91% (82/90).
  - After the changes: 100/100 over 2 trials. This includes 5 cases written after tuning to check that the gains generalize.
  - The report is written to `00 Maestro/Avaliacao de voz.md`.
- Desktop `continue_steps`: "voltar para a tela anterior" (navigate inside the app) was treated like "voltar para o Excel" (bring the window forward). It now goes to the app pilot unless the phrase is about the window itself. Found by `eval_conversations.py` after the Maestro reworded a subtask.
- Conversations now feel like chatting with an assistant:
  - Every conversation is saved to `memory/sessions/<id>.json` with its requests, replies and the windows, tab, project and folder left open. The sidebar lists conversations, and clicking one reopens it and restores its context.
  - Each request ends with a natural assistant reply written by `core/reply.py` (for example "Feito! Entrei em Acessibilidade…"), not just "Tarefa concluída". The voice speaks this reply only when it adds something.
  - Small talk ("valeu", "oi") gets its own short message and no longer gets attached to the previous request, typed or spoken.
- Fixed root causes found in real use:
  - The resolver only consulted the conversation when the request had words like "agora" or "esse". With Settings open, "clica em sistema" became a new request and reopened a Settings page. Now, when something is open and no other app is named, the model decides whether the request continues it.
  - A command was never supposed to become a "question", but the resolver could answer "abrir o Excel" with "já está aberto aqui". It now acts on the command. A new request also no longer carries the previous target ("abre outro bloco de notas").
  - When an app was already open in the conversation, Desktop reopened it from scratch, so Excel went back to its start screen. Desktop now continues in that window (`core/routing.py`, shared by the app and the evaluation) unless the user asks for another one. "Abre o Excel" with Excel open only brings it to the front.
  - App routines could only open the app. "Abre o Excel e preenche…" and "abre a calculadora e calcula…" now open the app and hand the rest of the request to the app pilot. The pilot has a new `write` action that types where the cursor is, with Tab/Enter, for spreadsheets and documents.
  - Notepad: the blank-document check looked at the foreground window, which is often not Notepad right after it opens. It now finds the Notepad window by title, opens a new tab if needed and types there. Known apps (`notepad.exe`, `excel`, `calc`, `code`, `ms-settings:`…) open directly instead of being typed into the Start menu.
  - Settings: page matching uses whole words ("tema" matched inside "sistema" and opened Colors). Requests to click or toggle something go to the pilot, and more pages are mapped. A new policy check rejects a Desktop plan when the request asks for a click and no step clicks; such plans used to be reported as completed.
  - App names have one canonical key (`settings` = `configurações` = `Configurações do Windows`), and windows the user has closed drop out of the conversation.
  - FILE safety audit: a system path cited in a blocklist or a protective comparison inside generated code is no longer treated as touching that path. Real use, such as `rmtree("C:/Windows/…")`, is still blocked.
- `scripts/eval_conversations.py` runs 28 multi-turn scenarios across Settings, Excel, Notepad, Calculator, YouTube, a shop, a code project, folders, closing apps and small talk. Each scenario runs the real resolver, Maestro, routing, agent plans and policy checks without executing anything on the PC. Result: 28/28 passed, US$ 0.15 per run. `--vault` writes the report to Obsidian.
- Voice mode, second pass (after real use: words that were never said, wrong apps, robotic and repeated speech):
  - Brazilian voice dictionary in the vault (`70 Dicionario/`): 7 notes, 310 rows, about 1,200 spoken variants. It covers app and site nicknames, colloquial ways of asking, modern slang, fillers to ignore, numbers and time, PC terms, and common transcription confusions such as "google escute" = VS Code and "Windows" ↔ "YouTube". `core/lexicon.py` reads it and reloads it when a note changes, so the user can teach new words in Obsidian.
  - Transcription:
    - Removed the app-list prompt that made Whisper "hear" names nobody said.
    - Beam search 5, `no_repeat_ngram_size` (fixes "meu, meu, meu"), and stricter no-speech/log-prob filters that drop ghost segments.
    - `large-v3-turbo` was measured at 16.5 s per phrase on this CPU, so the model stays `small` (about 2.7 s).
  - Understanding step (`core/voice/understand.py`) between transcription and execution:
    - Corrects the utterance with the dictionary and the conversation, drops noise, and classifies it as command, chat, stop, unclear or noise.
    - Writes the immediate spoken reply.
    - When unsure it asks once with its best guess, and "sim" runs the guess. It never runs a guess on its own.
    - Simple "abre o X" phrases heard with high confidence skip the model and get an instant reply.
  - Natural voice: Piper neural TTS runs locally in pt-BR (voice `cadu`, about 0.3 s per sentence) and can be interrupted. Windows SAPI is now only a fallback.
  - Replies are short, conversational and varied, and recent replies are not repeated. The agent asks "didn't catch that" only once. After a task it speaks only when there is something to tell (data it read, or a failure).
  - Two ways to talk:
    - Microphone button works like a voice message: click, talk, send. A recording bar shows the timer, levels and Cancel.
    - "Conversa" keeps the microphone open. Each utterance becomes a request with an instant spoken acknowledgement, and requests run in a queue while you keep talking. "para" stops and clears the queue; "para de ouvir" turns live mode off. The microphone ignores the agent's own voice and its echo.
  - The UI shows "Ouvi: …" (what the microphone heard) and the agent's spoken replies in the conversation. The hotkey (default `Ctrl+Alt+V`) is active from app launch.
- Routing fixes found in voice use:
  - "configurações do Windows" (and pages such as Bluetooth, Wi-Fi, sound and display) opens directly with `ms-settings:`.
  - Naming an app or site that is not open in the conversation is always a new request. Previously, with YouTube open, "configurações" became YouTube's settings.
  - Two-word commands like "abre youtube" are no longer blocked as vague.
  - A new full request no longer gets glued onto a pending clarification.
  - POL-001 no longer rejects "open" steps that carry a label in `text`.
- Review fixes:
  - Typing no longer wipes the user's clipboard (`core/clipboard.py` restores it).
  - The observer only records a window or tab after confirming it is the app or site that was opened, so it can never adopt one of the user's own tabs or windows.
  - `.ai_versions/` gets its own `.gitignore`.
  - The voice queue has a lock, its retry watchdog is bounded with daemon timers, and a guess is kept only when the question was actually asked.
- App pilot (`core/app_pilot.py`, action `app_task`) works like the browser pilot but inside any app window. Each turn it reads the window through UI Automation (`browser_uia.snapshot(app=True)`), then clicks, double-clicks, types, presses keys or scrolls, and falls back to vision when the app exposes little.
  - Desktop continuations ("now play that song below", "now calculate 12 times 7") use it on the window from the conversation.
  - Tested on Calculator: 12 × 7 = 84. The pilot saw a wrong digit on the display and corrected it.
- Voice mode (`core/voice/`, `desktop/voice.py`):
  - The global hotkey (default `Ctrl+Alt+V`) or the mic button records one utterance and stops when you stop talking. If the hotkey is taken, it falls back to `Ctrl+Alt+M` and `Ctrl+F9`.
  - The utterance is transcribed locally with faster-whisper (`small`, int8, Portuguese) and enters the same conversation as typed text.
  - The reply is spoken with the Windows pt-BR voice (SAPI, Microsoft Maria): the result, clarification questions and errors. After a question it listens again for the answer.
  - Saying "para" during a run stops it.
  - UI: a "Voz" toggle, a mic button with a level ring, and the listening/transcribing state.
  - Tested by turning Windows TTS output into audio files: 4 of 4 phrases were transcribed correctly in 2.5–3.4 s each on CPU. End to end through the real app: voice command → Calculator opened → spoken reply. Not yet tested with a real microphone utterance.
  - The `av` package (audio file decoding) is blocked by Windows Smart App Control on this machine. It is not needed for microphone audio, so it is stubbed if its import fails; no Windows policy is changed.
- Fixed: Windows 11 Notepad reuses its open window (with tabs), so "abra o bloco de notas e escreva…" could type into a document the user already had open. Notepad routines now ensure a blank, unmodified document first (`blank_document`), and typing requires one.
- Fixed: `write_file` ignored simulation mode and wrote files during dry runs.
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
