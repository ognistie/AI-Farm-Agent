# Changelog

All notable changes to AI Farm Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — 2026-11-04 (desktop app, closing for real, faster voice)

### Added
- **Authorization by effect** (`core/action_risk.py`). Clicking "Enviar", "Comprar", "Pagar", "Excluir", "Publicar" and similar, pressing Enter in a message field, or deleting a file now goes through a gate decided by the app, also inside the browser and app pilots, where only a prompt rule stopped it before. `execution.authorization` starts in `shadow`: nothing changes for the user and `memory/authorization.jsonl` records what would be blocked (the button label, never the typed text). In `enforce` the pilot stops before acting and asks for "confirmo".
- **Opening what already exists without a model** (`core/existing_targets.py`): the project's folder or site in the browser, a folder inside another, the folder changed at a given time, and bringing a folder window forward. An uncertain target becomes a question listing the real options.
- **Durable task record** (`core/task_ledger.py`). Each task writes its events to `memory/tasks/` before and after every step, so a crash no longer erases it. On the next launch an unfinished task is marked as interrupted, and a step with no recorded end is listed as having an unknown outcome. Nothing is repeated automatically. `execution.ledger` in `config.yaml` turns it off.
- `scripts/eval_live_turns.py` measures pauses, responses, delegation and interruptions on the real GPT-Live session, with a hard cap on accumulated spending.
- **Desktop shortcut.** `scripts/install_shortcuts.py` creates "AI Farm Agent" on the Desktop and Start menu, with its own icon, no console window and the same identity as the window, so it can be pinned to the taskbar. `scripts/setup.ps1` runs it. Without a console, output goes to `logs/app.log` and startup errors appear in a message box.
- **Only one instance.** Opening the app again brings the existing window forward instead of starting a second agent on the same microphone.
- `python scripts/latency_report.py --voice` reports the time from the end of speech to each stage, from `memory/voice_latency.jsonl` (times only, never speech or transcripts).

### Fixed
- **The agent kept running after closing.** On Windows, `os.execv` starts a new process and ends the original, so VS Code and the terminal lost track of the real app. The app now stays tied to its launcher. Closing the main window always quits, even with the mini chat open; Ctrl+C and closing the terminal also quit; the paid session closes and confirms usage, and a stuck library can no longer hold the process open.
- **The start of sentences was lost.** With headphones, the echo filter silenced the microphone while the agent spoke and for a moment after it. It now measures whether the microphone actually hears the agent, and only filters when it does.
- **Speech with no response.** If the model stays silent, the app answers. A cut-off request runs when the app has a guess and the model also treated it as a request, instead of "deixa comigo" with nothing happening.

### Changed
- **GPT-Live decides when to speak.** The prompt follows OpenAI's template, with listening sounds allowed and patience during pauses. The app answers only after 6 s of silence on a complete sentence (it was 2.5 s, which spoke over pauses to think), and its promise correction only applies to things claimed as done.
- The app waits for the end of the transcript before reading a turn: 1.1 s after the voice stops, or 0.3 s when the model already delegated. A shorter wait split sentences into pieces.
- Talking over the agent on headphones silences it after about 400 ms. The paid session stays open while a task runs, up to 120 s without conversation.
- A request the screen refused is retried in 1.5 s instead of 5 s.

---

## [Unreleased] — 2026-11-03 (GPT-Live: real-time conversation)

### Added
- **Real-time conversation in Conversa mode** (`core/voice/live_session.py`). GPT-Live 1 hears the microphone and speaks at once, using client delegation. Tasks still run through the app's understanding, queue and Maestro: a request runs even if the model never delegates, and a delegation alone never runs anything. Verified results go back to the model to be spoken.
- The paid session closes after 60 s without conversation and reopens when local detection hears speech or a result is ready. Echo is replaced by silence while the agent speaks; talking over it still interrupts.
- Settings switch "Conversa em tempo real com GPT-Live". When off, Conversa stays fully local.

- Obsidian vaults open directly through `obsidian://open?vault=NAME` (`core/obsidian_vaults.py`), without clicking on the screen. Only registered vaults open, and an uncertain name becomes a question.
- `memory/voice_conversation.jsonl` keeps counts per session (interruptions, audio gaps, drops), never speech or transcripts.

### Changed
- **Privacy:** with the key set and the switch on, Conversa sends microphone audio, a conversation summary and task results to OpenAI while a session is open.
- Daily local voice quota raised from 600 to 1,800 seconds (about US$ 1.50).
- Fallback voice is now Piper instead of the Windows voice.
- Narration accepts small paraphrases, but never a changed number.

### Fixed
- **"Check the site" created a new project and "open it in the browser" edited its files.** The code agent only has create and edit tools, so it now does nothing unless creating or changing is asked for, and says how to open the result instead.
- **A "professional" site took 4.5 minutes and failed.** The answer passed the 16,000-token limit twice, because the retry asked for the same thing. Static sites now use medium reasoning, and after a cut answer the retry asks for a smaller project.
- **The browser opened `c/Users/...` as a website.** A local page becomes a `file:///` address, and only if it exists.
- **"LLM nao retornou nenhum step".** The file and data agents explain what they can do instead. A simulated task no longer writes a plan to the second brain.
- **The agent went to Windows Settings without being asked.** A misheard vault name ("rede Aurol") became a guess about network settings, and vague speech ("esse aí com o mouse em cima") became clicks there. Settings now need to be named by the person, pointing without a name becomes a question, and only a short "yes" to a guess the person actually heard runs it.
- **Speech cut off.** Playback now runs continuously with a small buffer, keeps the quiet start of words, and no longer mistakes a louder agent phrase for an interruption. A sentence ending in an open word ("com o mouse em") waits for the rest instead of becoming two requests.
- **False claims from the model.** "Vou clicar" with no task running is corrected aloud and stays out of the conversation context, which fed later wrong commands.
- **"Fechar o VS Code" closed the app and reported failure.** The pilot now treats a window that disappeared after an action as success when the goal was to close it.
- **Opening an app without getting the foreground.** The wait no longer runs the full 12 s with the window already open behind, and a new window is no longer refused as ambiguous when another window of the same app exists.
- **Every GPT-Live session was rejected.** The app sent `session.delegation: null`, which the API refuses with `invalid_type` before closing the connection. Sessions now use `{"type": "client"}`.
- **`ValueError` after a single failure.** A failed session left a pending reservation that blocked all later calls. It now stays counted as spent without blocking; the daily quota still limits the total.
- Provider error codes are now logged and shown instead of being discarded, and a session rejected before starting no longer counts as spent.
- After two failures in a row, narration stays local for 5 minutes and warns once, instead of at every reply.

---

## [Unreleased] — 2026-10-20 (speed, verified memory, desktop features)

Research on Claude Cowork, ChatGPT Work, realtime voice and agent memory, with sources: `docs/research/cowork-chatgpt-work.md`.

### Changed
- **Reasoning per agent** (`agent_thinking` in `config.yaml`). Routing, voice understanding, the conversation resolver and the final reply now answer without reasoning first. Generation, file reading and the pilots keep it.
  - Maestro, with `scripts/eval_routing.py` (24 real requests from history, 2 trials): median 3.12 s → 1.69 s with the same routing accuracy (32/48 vs 31/48; the difference is one unstable case).
  - Voice, with `eval_voice.py`: 54/54 both ways.
- **Leaner Maestro plan.** The `objectives` and `forbidden_assumptions` fields were dropped because no code read them, and the generic-text cleanup moved to code. Output went from 213 to 130 tokens per plan (−39%) with the same accuracy.
- **Second brain: only verified memory guides the agents** (`core/memory_gate.py`, idea from CoALA and MemGuard).
  - A reference note is used only with `verificado: sim`, meaning it succeeded in a real run of the same agent. Each note carries its success and failure counts and last-run date.
  - 228 of 255 references had never been proven. They moved out of the vault to `memory/vault_arquivo/hipoteses` and return automatically when a matching real run succeeds.
  - A note that fails more than it succeeds is demoted.
  - Every run updates the matching note.
  - `00 Maestro/Mapa de roteamento` is generated from real runs.
- **Voice:** a short chime when speech ends ("ouvi"), so there is no silence while transcribing (`voice.earcon`).
- **Config:** `config.yaml` at the repository root is now found from any working directory. Running from `ai-farm-agent/` used to silently fall back to defaults.

### Added — desktop app (ideas from Claude Desktop, ChatGPT Desktop, Cowork and Work)
- **Settings** page (Ctrl+,):
  - custom instructions applied to every request, as preferences that never widen permissions;
  - "review the plan before executing";
  - interruption and chime toggles;
  - splash screen and mini chat toggles;
  - the list of shortcuts.
  - Stored in `desktop/data/settings.json`.
- **Quick access from any app:** Alt+Space opens the mini chat with the cursor in the request box (`ui.quick_hotkey`).
- **Attachments:** "+" button and drag and drop. Files enter the conversation, so "resume esta planilha" reads them. PDF and Word are read only when `pypdf` / `python-docx` are installed.
- **Plan review:** Execute / Cancel before touching the PC, for typed requests (voice already confirms out loud). Stop releases a waiting plan.
- **Conversations:** search, rename, and delete. Deleted conversations move to `memory/sessions/_excluidas`, so they can be recovered.

### Added — tooling
- `scripts/eval_routing.py` evaluates Maestro routing against real history.
- `scripts/brain_verify.py` verifies the vault against history (`--apply`).
- Smoke suite `test_round9_brain_speed_app` (22 checks). Four older checks were updated to the verified-memory contract.

---

## [Unreleased] — 2026-10-09 (fluid conversation)

Measured on today's runs.
- Every follow-up such as "clicar em Área de Trabalho" or "pausar o vídeo" paid a Maestro call (2.2–3.3 s) just to decide "continue in the open app".
- "Summarize the spreadsheet you just made" took 125 s and 19 model calls, then failed while reading the Excel grid on screen.

### Changed
- **Continue without the Maestro.**
  - An action inside what is already open (click, open an item, play, pause, go back, scroll, maximize, search on the open site) goes straight to the agent that owns the target (`continue_plan`). It saves ~2.5 s per conversational follow-up.
  - Creating, writing, summarizing, chaining another app or ambiguous requests still go to the Maestro. Plan policies still apply.
- **Questions about what the assistant created** read the file, not the screen (`core/artifact_qa.py`).
  - The session now remembers created files (spreadsheet, site, script, document).
  - "Resume a planilha", "quanto deu o total?" or "me explica esse site" are answered in one call from the file content, which is treated as data.
  - On today's cash-flow spreadsheet the answer took 5.2 s with every total correct, against 125 s and a failure before.
- **The pilot writes the user-facing sentence** (`say`) in its last turn. It becomes the assistant's reply without the extra reply call (~1.5 s faster to the spoken result).
  - Pilots also stop after 60–75 s with a clear message instead of looping.
- **Voice acts on its best guess** when something is open and the guess is a light action ("clica na pasta Relatorios"). The pilot checks the screen and says what it found. Consequential actions (send, delete, buy…) still ask first.
- **Speculative transcription.** A 0.3 s pause in speech already starts transcribing, while the 0.8 s end-of-speech check runs. If speech continues, the early result is discarded. This saves ~0.5 s per utterance.

### Fixed
- **Summarizing a larger spreadsheet failed.**
  - On a two-year cash-flow file, the reader model used its whole 1,200-token budget doing the arithmetic in its reasoning and returned an empty answer. The request then fell through to the screen pilot, which cannot read the Excel grid (30 s, failure).
  - The app now computes the totals itself (sum, count, largest and smallest value with the row label, per sheet and column) and gives them to the model first. The response budget is 4,000 tokens.
  - If the file still yields no answer, the assistant says so instead of falling back to the screen pilot.
  - Real file: the summary takes 4.9 s and "quanto deu o lucro de 2026?" 2.1 s, both with exact figures.
- Opening Excel or Word: the start screen is dismissed with Esc, which opens the blank document (Ctrl+N alone left it on the start screen).
- Adaptive wait: an app that never reports "idle" (WhatsApp, UWP apps) counts as ready once it is stable and responding. "Abrir o WhatsApp" took 9 s.

### Added
- Smoke suites `test_round7_fluid_conversation` (19 checks) and `test_round8_spreadsheet_reader` (7 checks).

---

## [Unreleased] — 2026-10-09 (conversation, memory, second brain)

Found while testing live voice and text conversations. Every fix targets the whole system, not a single task.

### Fixed
- **Typing into the wrong window.**
  - Before pasting, `app_type` now checks that the target window is really in the foreground.
  - Windows refuses focus to background apps (for example when the user talks to the assistant while working in another app), so Ctrl+V used to land elsewhere while the step reported success.
  - The window is now raised with the input queue attached (`_bring_to_front`). If focus is still refused, the step fails with a clear message and nothing is typed.
- **Waiting for the wrong app.** After `app_search`, the adaptive wait only ends when the window of *that* app is in front. When the Start menu closed, another window came forward and ended the wait for Obsidian in 0.4 s.
  - `focus_window` now waits up to 8 s for slow apps (Obsidian, Teams, Spotify) and confirms focus.
- **Conversation memory lost content.**
  - The context cut every request to 160–200 characters, so "try again with the same message" reached the agent without the message.
  - Each turn now stores its literal content (message, dictated text, query, recipient) from the plan. Recent turns appear in full.
  - When the context is over budget, the oldest turns are dropped instead of the newest turn and the open windows.
  - Voice understanding and the resolver copy referenced content into the request, because the executor does not see the conversation.
  - "Escreva sobre X" now means composing a text about X rather than typing the word X.
- **Failure replies guessed causes.** One reply said "it doesn't seem to be installed" for a focus timeout. Failures now record the step that really failed, and the reply only states what the result says.
- `memory_agent`: the test/debug filter regexes contained backspace characters instead of `\b`, so they never matched.

### Changed
- **Live conversation, closer to Siri, Alexa and ChatGPT voice.**
  - Turning it on says "Como posso ajudar?" right away (≈0.4 s). The voice model is loaded and warmed at launch.
  - **Barge-in:** talking over the assistant stops it within ~240 ms, and the speech is recorded from the start instead of being discarded. Detection is relative to the speaker echo, so the assistant's own voice does not interrupt it (`voice.barge_in`).
- **Second brain cleanup.**
  - Automatic execution logs are no longer injected into agent prompts. They were one in three retrieved references, often duplicated, obsolete or false successes.
  - The vault keeps the 40 most recent per folder. Older ones move to `memory/vault_arquivo` (315 moved).
  - 9 reference notes were fixed to today's paths: Word/Excel blank document, Settings, calculator, Spotify, unknown apps, YouTube/Google first result.
  - 9 were removed: duplicates, notes about old failures, and selector-based web steps.
  - Two web playbooks no longer teach `web_click` selectors.
  - Four new lessons cover the failures above.

### Added
- `scripts/vault_audit.py` checks reference notes for obsolete mechanisms, empty paths and duplicates (`--apply` moves them out of the vault).
- `eval_voice.py` has 4 new held-out cases: resending the same message with a change, resending without a change, "write about X", and literal dictation.
- Smoke suite `test_round6_conversation_memory_vault` (20 checks).

---

## [Unreleased] — 2026-10-09 (latency)

Measured on the real history before the change (180 runs, 2–8 Oct): opening an app or site had a median of 7.4 s (P90 15.7 s), and opening Excel took 18–31 s.

### Changed
- **"Open <app/site>" without the model.**
  - When the whole request is "abrir" plus the exact name of an app or site from the Obsidian dictionary (`70 Dicionario/Apps e sites`), the Maestro builds the plan directly. It saves one model call (~2–3 s).
  - The plan goes through the same acceptance policies.
  - Anything more ("e pesquisa…", "e cria…", a folder, a file) or something already open in the conversation still goes to the Maestro.
- **Adaptive waits.** The fixed "aguardar N s" in the app routines is now a ceiling.
  - The wait ends as soon as the window that came to the front is ready: it is not hung, its process is idle for input (`WaitForInputIdle`) and its title has been stable for 0.4 s.
  - With no new window, it waits the full time as before.
  - `app_search` uses the same check instead of a fixed 2 s.
  - Simulation mode no longer sleeps.
- Opening Excel or Word creates the blank document with Ctrl+N (`blank_document`) instead of a vision click (one model call).
- Opening WhatsApp or Teams without a contact or message no longer searches for a chat with three vision clicks.
- A site with a ready URL opens directly instead of through the browser pilot.
- The assistant's reply starts before the run is written to Obsidian.
- The speech model loads a few seconds after launch (`voice.preload_on_launch`), so the first voice command does not wait for it.
- Long generations (spreadsheet, site, plan) show live progress in the status line ("Montando a planilha · 2.400 caracteres") instead of a static label for 30–70 s.

### Added
- Each history entry records model time (`metrics.llm_ms`, total and per agent) and time per phase (`timing`: resolve, Maestro, agent plan, steps).
- `scripts/latency_report.py` gives the median and P90 per request type from the real history, plus where the time went.
- `scripts/bench_stt.py` measures local speech-recognition time and accuracy with phrases spoken by the local voice. It needs no API.
- `voice.beam_size` (now 1) and `Transcriber.chunk_length` are configurable. In `bench_stt.py`, with 32 utterances on an idle machine:
  - `small` beam 5: 3.25 s per utterance, 19.3% WER.
  - `small` beam 1: 2.75 s, 20.4% WER. This is −0.5 s per voice command, and the accuracy difference is about one word in 32 phrases.
  - `base`: 1.0 s but 32.5% WER, so rejected.
  - A shorter audio window did not help.
- Smoke suite `test_latency_round5` (21 checks).

### Evaluated, not changed
- Voice understanding stays on Sonnet 5. `eval_voice.py`, 50 cases, 1 trial each:
  - Sonnet 5: 50/50 correct, 50/50 speech style, median 1.38 s, US$ 0.087.
  - Haiku 4.5: 50/50 correct, 48/50 speech style, median 1.21 s, US$ 0.095.
  - −0.17 s does not pay for worse replies and a higher cost.

---

## [Unreleased] — 2026-10-08

### Added
- Intro screen: the brand mark over a slow-moving peach, orange and lilac gradient, then "press any key or click to enter". It runs in its own window on top of the already-maximized app, covering exactly the maximized area (the screen minus the taskbar). On entering, only that window fades out, so nothing is resized and the image never breaks. It can be turned off with `ui.splash: false`.
- Mini chat (`desktop/qml/components/MiniChat.qml` and `desktop/window_mode.py`):
  - When a task is running and another app comes to the front, the main window minimizes without taking focus. The current conversation continues in a card in the bottom-right corner.
  - While the agent works, the card takes no focus or clicks (`WindowTransparentForInput` and `WindowDoesNotAcceptFocus`). When the task ends it becomes interactive again, so you can keep the conversation going or reopen the full window.
- Global stop hotkey `ui.stop_hotkey` (default `Ctrl+Alt+X`).
- Smoke suite `test_window_mode` (18 checks).

### Changed
- The desktop UI moves to a light theme taken from the launch video:
  - white surfaces and neutral greys;
  - black primary action;
  - one blue accent;
  - green status circles;
  - a new four-square brand mark, also used as the window and taskbar icon;
  - a light native title bar.
- The home screen now reads "Como posso ajudar?". The composer has a soft blue focus halo, and voice recording uses the accent color.

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
- App pilot: calculators and numeric input are typed in one action (`write "128*47\n"`) and the result is read from the display. The pilot also switches strategy (keyboard first) when the window does not react. Before, it clicked digit buttons one by one, mis-entered them and hit the 12-turn limit (12 model calls, task failed); now it takes 2 calls.
- `scripts/bench_cost.py`: cost benchmark on the same tasks for AI Farm Agent (measured), Claude Cowork and ChatGPT Work (estimated):
  - **AI Farm side:** every task runs for real through the voice path. Each model call is recorded (input, output and cache tokens, cost), along with each executed action and the size of each text screen read.
  - **Competitor side:** API-equivalent cost of a screenshot agent that takes the same number of steps we needed, priced at each provider's public API rates, in a "lean" scenario (favorable to them) and a "typical" one. All assumptions are written into the report.
  - The report breaks down where the savings come from and compares monthly subscriptions. It is written to `00 Maestro/Benchmark de custo.md`.
- Skills from the AIWorkbench catalog now reach the agents (`core/skills.py`):
  - The 15 notes in `30 Skills/` were rewritten as usage manuals. Each note has:
    - what the skill does;
    - when it activates (`ativa_quando` request words, and `sempre_para` agents that always get it);
    - how each agent applies it, as concrete lines such as "Code Agent: semantic HTML and keyboard-usable controls";
    - the catalog rules, what to check before finishing, and the catalog workflow.
  - On every request, an agent gets its 1–3 most relevant skills (Maestro up to 2, browser/app pilots 1 short), and only the lines meant for that agent. Lines are kept whole within a size budget.
  - Code project edits (`plan_edit`) now also consult the vault and skills.
  - Applied skills are logged ("Skills aplicadas"), stored in the history entry (`agent_skills`) and listed in the plan note. Context blocks are budgeted as whole blocks, and only what reached the prompt counts as consulted.
  - Each agent note lists its skills and when they activate. Skills are reference only and never widen permissions.
  - `scripts/eval_skills.py` runs the same Code Agent requests with and without skills and grades the generated code by rule:
    - result: 28/28 criteria with skills vs 27/28 without, over 2 trials × 2 tasks;
    - the Code Agent was already near the ceiling on these checks, so this is no regression rather than a proven large gain.
  - `eval_conversations.py` stays at 28/28.
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
