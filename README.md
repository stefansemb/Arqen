# Arqen

**A local AI assistant for Windows, with a Mission Control for agents, tasks
and workflows.**

Arqen is a desktop app built with PyQt6. You chat with it by text or voice,
hand work to agents that run in the background, and give those agents exactly
the tools they need: your files, the web, GitHub, Google, Discord, Telegram or
any MCP server. Anything that can't be undone waits for your approval.

It is built to be local, controllable and extensible. Cloud models are
optional; a local model through Ollama or LM Studio works as the base.

*[Svenska](README.sv.md)* · The interface speaks English or Swedish
(Settings → Language).

![Connections: give an agent access to packages of tools](docs/images/connections.png)

## Features

**Chat and voice**

- Chats you can open, rename and delete; replies stream in and can be stopped
  mid-answer.
- Neural voice through Edge TTS (`en-GB-RyanNeural`, or `sv-SE-MattiasNeural`
  in Swedish) and speech recognition through faster-whisper.
- A voice panel with an animated ring that shows whether Arqen is idle,
  listening, thinking or speaking.
- A stats panel with tokens and cost for the chat, the latest reply and in
  total. The cost is the provider's own figure, not an estimate.

**Mission Control**

- Tasks, multi-agent workflows, schedules (daily, weekly, monthly or once) and
  an activity log.
- Agents with their own tool rules. Every task runs in its own Arqen, so an
  agent's limits never affect your chat.
- Timeouts, recovery, retries and stored results for tasks.
- One approval bar at the top of every view collects everything that is
  waiting for you.

**Memory**

- Long-term memory with source, status and confidence.
- Arqen **suggests** memories when you tell it something lasting; you approve
  or reject them under Memory. Only approved memories are used.
- **Reflect**: Arqen reads recent tasks and chats and suggests lasting lessons,
  also as suggestions.
- "Remember that …" saves right away.

**Tools and safety**

- Tools for the system, windows and programs, files in your workspace,
  documents (PDF, Word, Excel), the web, a built-in browser, voice and image
  generation.
- Approval is required to write, delete, move or undo files, to create images
  (which costs money) and to close programs.
- A Tool Gateway with risk levels, rules per agent and a local log of every
  tool call, including its cost.
- API keys are read only when a tool runs and are scrubbed from everything a
  tool returns. Memories that look like passwords or keys are never stored.

![The Tool Gateway catalogue](docs/images/tools.png)

**Connections**

- **GitHub** (personal token): repos, issues and pull requests; creating an
  issue needs approval.
- **Google** (OAuth with your own Desktop client): search and read Gmail, see
  upcoming Calendar events, search and read Drive files. Mail drafts and
  calendar events are created with approval; no mail is ever sent.
- **Discord** (webhook) and **Telegram** (bot): send messages with approval,
  and optional notifications when tasks finish or fail.
- **MCP servers**: add an address (e.g. Zapier's MCP URL) or a local program,
  and the server's tools become Arqen tools. They need approval unless the
  server marks them read-only.

**Models**

- Ollama / LM Studio, OpenRouter, OpenAI, Gemini and Claude.
- Ready-made profiles: Private (Ollama), Fast (OpenRouter), Important (OpenAI)
  and Creative (Gemini).
- An optional fallback provider if the first one doesn't answer (off by
  default).

## Getting started

Arqen is built for **Windows** and needs **Python 3.10 or later** (developed on
3.12).

```powershell
git clone https://github.com/stefansemb/Arqen-Desktop.git
cd Arqen-Desktop
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m arqen.ui
```

Then, in the app:

1. Open **Settings** (bottom left) and pick a profile, or choose a provider
   and model yourself. Paste your API key and press **TEST CONNECTION**, then
   **SAVE**. For a fully local setup, start Ollama and choose *Private –
   Ollama*.
2. Under **Settings → Workspace**, choose the folder Arqen may read and write
   files in. Empty means the application folder.
3. Say hello in **Chat**. Try "What's in my workspace?" or
   "remember that I prefer short answers".

Good to know:

- **ffmpeg** must be on your `PATH` for the voice (playback and the level
  meter). Install it with `winget install Gyan.FFmpeg`.
- The first time you use the microphone, faster-whisper downloads its
  speech model (`small` by default). Set `ARQEN_WHISPER_MODEL`,
  `ARQEN_WHISPER_DEVICE` (`cpu` or `cuda`) or `ARQEN_WHISPER_COMPUTE_TYPE` to
  change it.
- Settings are saved in `config/arqen.json`; `config/arqen.example.json` shows
  the format. API keys are kept apart in `config/arqen-secrets.json`. Neither
  is ever committed.
- Chats, memory, tasks and the tool log live in `data/`.
- For Google, create your own OAuth client of type *Desktop app* in Google
  Cloud Console; the connection dialog explains where. While the client is in
  testing mode, Google makes you sign in again every 7 days.

The core without the window starts with `python -m arqen`. Check a local
provider with `python -m arqen.doctor`.

## Local API

The API is a separate process and is not started by the app:

```powershell
python -m arqen.api --port 8765 --token <your-token>
```

It listens on `127.0.0.1` only. The token can also be set with the
`ARQEN_API_TOKEN` environment variable. Without a token no sign-in is
required, so always set one if anything but you can reach the machine. Every
call except `/api/v1/health` then needs `Authorization: Bearer <token>`.

Endpoints under `/api/v1` cover sessions and messages, status, tasks, agents,
approvals, schedules, workflows and tools. See
[MOBILE_API_PLAN.md](MOBILE_API_PLAN.md) (in Swedish) for the full list and
what is not finished yet.

## Development

```powershell
python -m compileall -q arqen
python -m pytest -q
```

- `tests/conftest.py` points the workspace, data and config folders at a
  temporary directory, so tests never touch your chats, memory, tasks or keys.
  Don't remove it.
- All UI text goes through `tr()` in `arqen/ui/strings.py`. Write it in
  English in the code and add the Swedish translation to the table there.
- New tools need a category and a name in English and Swedish in
  `arqen/ui/tool_catalog.py`; a test checks this.

## Status

Chat, voice, Mission Control, memory with suggestions and reflection, the
Tool Gateway and the connections (GitHub, Google, Discord, Telegram, MCP) work
locally. Next up: approvals through the API and a mobile client. The working
notes are in [HANDOVER.md](HANDOVER.md) (in Swedish).

> The repository is called Arqen-Desktop for historical reasons. The old
> desktop version is no longer developed; its last release is kept as the tag
> `arqen-desktop-legacy`.

## License

[MIT](LICENSE) © 2026 Stefan Semb. You may use, change and share Arqen,
also commercially, as long as the copyright notice and license come along.
