# Changelog

All notable changes to AI Farm Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
