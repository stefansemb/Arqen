# Changelog

## 1.0.1 (2026-09-28)

- A smaller download: six images made with Arqen had been included in the
  repository by mistake. They are gone, and the download shrinks from almost
  10 MB to under 1 MB. Nothing else changes.
- The install guide names the folder the zip unpacks to for any version.

Already on 1.0.0? Nothing to do: the images are not used, and your own
generated images stay in `data/generated`.

## 1.0.0 (2026-09-28)

The first public release of Arqen: a local AI assistant for Windows with a
Mission Control for agents. Download *Source code (zip)* below, unzip it and
double-click `install.cmd`.

### Chat and voice

- Chats that stream, can be stopped mid-answer, and are saved, renamed and
  deleted from the chat list.
- Ollama / LM Studio, OpenRouter, OpenAI, Gemini and Claude, with ready-made
  profiles and native tool calling.
- Neural voice through Edge TTS and speech recognition through faster-whisper,
  with an animated voice ring and a stats panel with tokens and the
  provider's own cost figure.

### Mission Control

- Tasks, multi-agent workflows, schedules (daily, weekly, monthly or once)
  and an activity log.
- Agents with their own tools and approval rules; every task runs in its own
  engine, so an agent's limits never reach the chat.
- One approval bar at the top of every view for everything waiting on you.

### Memory

- Long-term memory with source, status and confidence. Arqen suggests
  memories; only the ones you approve are used.
- Reflect: lasting lessons from recent tasks and chats, also as suggestions.

### Tools, safety and connections

- 52 built-in tools: system, windows and programs, workspace files,
  documents, the web (with tech news and release notes), a built-in browser,
  voice and image generation.
- Approval for anything that can't be undone. A Tool Gateway with risk
  levels, rules per agent and a log of every call with its cost.
- Keys are read only when a tool runs and are scrubbed from everything a tool
  returns.
- Connections: GitHub, Google (Gmail, Calendar, Drive), Discord, Telegram and
  any MCP server, handed to agents with one click.

### On your phone

- Settings → Mobile starts Arqen's API over Tailscale and shows a QR code.
  Chat, approve tools and Mission Control's approvals, and follow your tasks
  from the phone's browser.

### Languages

- English (the default) and Swedish, for the interface, the model's answers
  and the voice (Settings → Language).

### Install

- `install.cmd` sets up a private Python environment, the packages, the
  browser for the web tools and a Start menu shortcut, and offers Python and
  ffmpeg through winget when they are missing.

Arqen is MIT-licensed.
