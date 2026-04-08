# Contributing to AI Farm Agent

> *"I can only show you the door. You're the one that has to walk through it."*

Thanks for your interest in contributing! Here's how to get started.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/AI-Farm-Agent.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Push: `git push origin feature/your-feature`
6. Open a Pull Request

## Development Setup

```bash
cd AI-Farm-Agent/ai-farm-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pywinauto easyocr
python -m playwright install chromium
copy .env.example .env
# Edit .env with your API key
```

## Project Rules

1. **API first** — If it can be done with code, don't click pixels
2. **UIA before Vision** — pywinauto before Claude Vision
3. **Vision is last resort** — Only when UIA fails
4. **No fixed waits** — Use `wait_for_window()` or `wait_for_element()`
5. **All imports explicit** — Never assume a module is available
6. **Haiku for simple, Sonnet for complex** — Cost optimization
7. **JSON pure** — Agent responses are JSON, no markdown
8. **Max 10 steps per agent** — Less is better
9. **Log everything** — Action Logger records all actions
10. **Test before integrating** — Each transition tested individually

## Adding a New Agent

1. Create `agents/your_agent.py` following existing patterns
2. Register in `ui/server.py`
3. Update `agents/maestro.py` prompt

## Adding a New App

1. Map controls: `uia.list_controls("AppName")`
2. Create `state_maps/appname.json`
3. Add to `CONTROL_MAPS` in `core/uia_driver.py`
4. Add routine in `agents/app_routines.py`

## Commit Messages

Use clear, descriptive messages:
```
feat: add Outlook agent support
fix: Teams chat filter not working
docs: update README with new actions
refactor: simplify interaction layer cascade
```

## Questions?

Open an issue or reach out to [@ognistie](https://github.com/ognistie).
