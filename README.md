# Kali — AI Companion

A cat-themed, always-on desktop companion that lives on your second
monitor. Not a chatbot — a presence that researches, renders, and acts on
your behalf. Voice and text are first-class equals. Local-first by default.

> Status: **Phase 4 — complete.** Screen capture via Wayland portal,
> vision provider (LLM multimodal + OCR), organize_folder, WidgetGrid,
> Mermaid diagram rendering, Dota 2 builds via OpenDota API,
> anti-spoiler game info search, DotaHeroCard widget, gaming profile.
> **Phase 5 (Advanced voice) — in progress.** Wake word detection
> implemented, UI indicators, multi-backend capture research.

## What Kali does

- Sits fullscreen on a second monitor (or a dedicated device), always
  present while you code, game, or work.
- Listens and speaks with parity: talk to it while your hands are busy, or
  type when you need precision.
- Goes beyond conversation: runs tests, creates git worktrees in parallel,
  launches apps, organizes folders, researches the web, renders mockups and
  documents, and looks at your screen — only when you allow it.
- Works with or without [nanobot](https://github.com/fr4j4/nanobot): a
  self-contained agent runtime is included, and nanobot is an optional LLM
  provider for those who already run it.
- Local-first: offline speech recognition (Vosk), local TTS (Piper + numpy
  effects, no ffmpeg required). The LLM is configurable (local or cloud).
- Internationalized from day one: English and Spanish, with room for more.

## Project name

Kali is named after the cat. Every module carries a cat-themed name to give
the project personality and to make each subsystem independently
identifiable — so that any of them can grow into its own project later with
zero rename cost. See [docs/GLOSSARY.md](docs/GLOSSARY.md) for the full
naming scheme.

## Repository layout

```
ai-voice-companion/
├── docs/                ← start here
│   ├── VISION.md
│   ├── ARCHITECTURE.md
│   ├── COMPONENTS.md
│   ├── GLOSSARY.md
│   ├── I18N.md
│   └── PROTOCOL.md
├── kali-shell/          ← Electron shell (the cat's home)
├── kali-web/            ← React + Vite frontend (the cat's face)
├── kali-core/           ← Python sidecar (the cat's body)
│   └── kali_core/
│       ├── voice/       ← kali-voice (TTS)
│       ├── ear/         ← kali-ear (STT)
│       ├── mind/        ← kali-mind (agent + LLM providers)
│       ├── claws/       ← kali-claws (tools)
│       ├── gaze/        ← kali-gaze client
│       ├── canvas/      ← kali-canvas artifact spec
│       ├── collar/      ← kali-collar (permissions)
│       ├── nest/        ← kali-nest (sessions + memory)
│       └── yarn/        ← kali-yarn (WS protocol)
└── scripts/
```

## Documentation

Read these in order:

1. [docs/VISION.md](docs/VISION.md) — what Kali is and why it exists.
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — the three-layer model and
   data flow.
3. [docs/COMPONENTS.md](docs/COMPONENTS.md) — every module, its interface,
   and its origin.
4. [docs/GLOSSARY.md](docs/GLOSSARY.md) — the cat-themed naming scheme.
5. [docs/PROTOCOL.md](docs/PROTOCOL.md) — the WebSocket event contract.
6. [docs/I18N.md](docs/I18N.md) — the internationalization strategy.

## Running Kali

### Without Docker (native development)

**Quick start (Piper TTS, no compilation required):**

```bash
cp kali-core/.env.example kali-core/.env
# Edit KALI_LLM_API_URL with your LLM endpoint

./scripts/dev.sh
# → Open http://localhost:5173 in your browser
```

`dev.sh` auto-creates a Python venv, installs PyPI dependencies, and starts
both kali-core (port 8900) and the Vite dev server (port 5173). Screen
capture is not available in dev mode.

**With Qwen3-TTS (optional, higher quality voice):**

```bash
./scripts/build-qwen-cpp.sh cpu          # compile C++ inference binary
./scripts/download-qwen-models.sh        # download GGUF voice models
./scripts/dev.sh                         # start (set KALI_TTS_PROVIDER=qwen3)
```

**Production mode (Electron + screen capture):**

```bash
# Requires a Wayland session with Hyprland
./scripts/prod.sh
```

`prod.sh` builds the production frontend, compiles the Electron shell, and
launches kali as a native window.

### With Docker

```bash
cp docker/.env.example docker/.env
# Edit KALI_LLM_API_URL in docker/.env

docker compose -f docker/docker-compose.yml up -d --build
# → Open http://localhost:8080 in your browser
```

See [docker/README.md](docker/README.md) for GPU support, engine selection,
microphone setup, and advanced configuration.

## Roadmap

| Phase | Scope | Delivers | Status |
|---|---|---|---|
| **0 — Foundations** | Tauri/Electron shell, WS, STT/TTS, DirectLLMProvider, base frontend | Functional companion | ✅ |
| **1 — Agent + Tools** | AgentRuntime, `fs_*`, `run_command`, PermissionGateway, consent UI, themes, profiles | Agent with tools and permissions | ✅ |
| **2 — Dev Cases** | `run_tests`, `git_*`, `launch_app`, `web_search`, `web_fetch`, multi-session, Planner, Memory | "Ask it to run tests / create a worktree" | ✅ |
| **3 — Capture + Render** | Wayland ScreenCapture, `screenshot` tool, Canvas artifacts, vision provider, `organize_folder` | "Watch your screen and render mockups" | ✅ |
| **4 — Gaming** | Dota builds, anti-spoiler info, per-game widgets, refined profile, LLM vision | "In-match assistance" | ✅ |
| **5 — Advanced Voice** | Wake word, intra-segment PCM, X11/Win/macOS capture, packaging | Polished open-source release | ⬜ |

## Tech stack

| Layer | Tech | Why |
|---|---|---|
| Shell | Electron + TypeScript | Mature, multiplatform, native tray support |
| Frontend | React + Vite + TypeScript | Canvas ecosystem, i18n support |
| Core | Python 3.12 + asyncio | Readable, reuses existing AI libraries |
| Protocol | Local WebSocket (JSON) | Low latency, documented contract |
| STT | Vosk (offline) | Offline, supports multiple languages |
| TTS | Piper in-process + Qwen3-TTS + HTTP | Local, high quality, modular |
| LLM | OpenAI-compatible + nanobot | Flexible, works with Ollama/Cloud |
| Capture | mss (Python) | Automatic platform detection (Wayland/X11/Win) |
| Permissions | JSON profiles + consent | Declarative and secure |
| i18n | react-i18next | Standard and browser-friendly |
| Build | `electron-builder` + `pyinstaller` | standard packaging options |

## License

MIT. See `LICENSE`.

## Status

This is a personal project with open-source intent. All phases from 1 to 4 are complete (text + voice I/O, agent with tools, permissions + consent, themes, profile switcher, dev tools, web tools, multi-session, Planner, Memory, Screen capture, Artifact rendering, and Gaming assistance). Phase 5 (advanced voice + portability) is partially implemented with wake word support. Contributions are not yet open while the core shapes stabilize, but issues and discussions are welcome.
