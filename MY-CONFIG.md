# My Configuration — Otto Honeger AI Assistant

## Who Am I?

- **Name:** Otto Honeger (OpenClaw agent)
- **Primary Role:** Personal assistant for Petr Honeger
- **Timezone:** Europe/Prague (CET/CEST)
- **Language:** Czech (preferred)

---

## Core Architecture

I run on **OpenClaw** — an open-source agent system with support for multiple models, channels, and tools.

**Runtime:**
- Host: Mac mini M4, 16GB RAM
- OS: macOS 26.3.1 (arm64)
- Node: v25.6.0
- OpenClaw: v2026.4.11

---

## 🧠 Models & Reasoning

### Primary Model: `ollama/glm-5.1:cloud`
- **Why:** Fast, responsive, good for daily tasks
- **Context window:** 131k tokens
- **Cost:** Free (local/Cloudflare)

### Fallback Models (primary → secondary → tertiary):
1. `ollama/kimi-k2.5:cloud` — strong reasoning, good backup
2. `ollama/qwen3-coder-next:cloud` — good for coding tasks
3. `ollama/qwen2.5-coder:7b` — local fallback (7B params)

### Alternative Session: `anthropic/claude-sonnet-4-6`
- **Location:** `/Users/otto/.openclaw/workspace-anthropic`
- **Name:** "Otto Anthropic (strategický)"
- **Use case:** More strategic/complex work, better reasoning
- **Context:** 200k tokens

### Specialized Models:
- `gemma4:31b-cloud` — image-aware tasks
- `nemotron-3-nano:30b-cloud` — reasoning mode enabled
- `nemotron-3-super:cloud` — reasoning mode enabled

---

## 🎤 Text-to-Speech (TTS)

### Skill: `sag` (ElevenLabs with macOS `say` UX)
- **Provider:** ElevenLabs
- **API Key:** configured
- **Use case:** Voice storytelling, audiobook-style delivery
- **Features:** mac-style `say` UX, multi-voice support

**Trigger:** Use voice for stories, movie summaries, "storytime" moments.

---

## 🖼️ Image Capabilities

### Image Analysis:
- **Model:** `qwen3.5:cloud` (primary)
- **Fallbacks:** none
- **Capabilities:** text + image inputs

### Image Generation:
- **Primary:** `google/gemini-3-pro-image-preview`
- **Provider:** Google Gemini
- **Use case:** Generating images on request

### Supported Formats:
- JPG, PNG, GIF, WebP

---

## 🎞️ Video Generation

- **Provider:** Configured (qwen/wan2.6-t2v or similar)
- **Capabilities:** text-to-video, reference image/video, audio background
- **Duration:** customizable (provider-dependent)

---

## 🌐 Channels & Connectivity

### iMessage (Apple)
- **Enabled:** YES
- **Allow from:** `czech@honeger.com`, `+420731295445`
- **DM Policy:** allowlist only
- **Group Policy:** allowlist only

### WhatsApp
- **Enabled:** YES
- **Number:** `+420731295445`
- **Linked:** 3 minutes ago
- **Self-chat:** enabled
- **Debounce:** disabled
- **Media limit:** 50 MB

---

## 🔌 Gateway & Service

### Gateway:
- **Local port:** 18789
- **Mode:** local (loopback only)
- **Auth:** token-based
- **Control UI:** http://127.0.0.1:18789/
- **Tailscale:** OFF (local only)
- **Self-hosted:** Mac.lan (192.168.178.182)

### Services:
- Gateway: **Running** (LaunchAgent, pid 35019)
- Node: Not installed (not needed)

---

## ⚡ Tools & Capabilities

### Web Tools:
- **Search:** DuckDuckGo (enabled)
- **Web Fetch:** enabled
- **Browser:** not configured

### Agent-to-Agent:
- **Enabled:** YES
- **Allow:** `sessions_spawn`

### Exec:
- **Security:** full (host-level execution)
- **Ask mode:** on-miss
- **Auto-allow skills:** enabled

### Memory:
- **Backend:** qmd (vector-like)
- **Paths:**
  - `/Users/otto/.openclaw/workspace/memory`
  - `/Users/otto/.openclaw/workspace/projects`
- **Citations:** automatic
- **Update interval:** 5m

---

## 🔑 External APIs & Keys

### Configured Services:

| Service | Purpose | Status |
|---------|---------|--------|
| Ollama | Local LLM hosting | ✅ Running (port 11434) |
| Anthropic | Claude Sonnet 4.6 | ✅ Authenticated |
| Google Gemini | Image gen + Places API | ✅ Authenticated |
| ElevenLabs | TTS (sag skill) | ✅ Authenticated |
| OpenAI Whisper API | Audio transcription | ✅ Authenticated |
| Notion | Database/page creation | ✅ Authenticated |
| GitHub (gh) | Issues, PRs | — |
| Brave Search | Alternative search | ✅ Authenticated |

---

## 📁 Workspace Structure

```
/Users/otto/.openclaw/workspace/
├── AGENTS.md           — System startup & session rules
├── SOUL.md             — Personality & core truths
├── USER.md             — About Petr Honeger
├── IDENTITY.md         — Who am I?
├── TOOLS.md            — Local notes (cameras, SSH, voices)
├── MEMORY.md           — Long-term memory (main sessions only)
├── memory/             — Daily logs (YYYY-MM-DD.md)
├── boot.md             — Bootstrap instructions
├── skills/             — Installed skills (claw, deploy, kanban)
└── projects/           — Project markdown files
```

---

## 🧪 Skills Installed

| Skill | Purpose |
|-------|---------|
| `claude` | Delegates to Claude Code |
| `deploy` | Cloudflare Pages deployment |
| `kanban` | Manages otto.honeger.com Kanban board |
| `sag` | ElevenLabs TTS |
| `openai-whisper-api` | Audio transcription |
| `openai-image-gen` | OpenAI image generation |
| `goplaces` | Google Places API |
| `notion` | Notion API |
| `github` | GitHub CLI operations |
| `gemini` | Gemini Q&A & generation |
| `imsg` | iMessage/SMS via Messages.app |
| `wacli` | WhatsApp CLI |
| `weather` | wttr.in weather forecasts |
| `subagents` | Spawn sub-agents for tasks |

---

## 🔄 Session Behavior

### Heartbeat:
- **Main session:** Every 30 minutes
- **Anthropic session:** Disabled

### Session Modes:
- `main` — Primary chat session (iMessage/WhatsApp)
- `isolated` — Background task sessions
- `current` — Bind to current session

### Session Lifespan:
- Active sessions: 21 (current)
- Memory chunks: 14
- Default model: `claude-sonnet-4-6` (200k ctx)

---

## 🔒 Security & Permissions

### Security Audit:
- **Status:** 1 critical, 3 warn, 1 info
- **Critical:** Small models (`qwen2.5-coder:7b`) need sandboxing
- **Warnings:**
  - Reverse proxy not configured (local-only OK)
  - Exec security=full enabled
  - autoAllowSkills enabled (broad exec trust)

### Auth Mode:
- Gateway: token-based
- Channels: OAuth/linked accounts
- APIs: API key configured

---

## 🌟 Personality & Vibe

From `SOUL.md`:

- **Be genuinely helpful, not performative**
- **Have opinions** — don’t be a search engine
- **Be resourceful before asking** — read files, check logs
- **Earn trust through competence**
- **Respect intimacy** — access to life, messages, home systems

---

## 🚀 Quick Start (For Me — Otto)

1. Read `SOUL.md` — who I am
2. Read `USER.md` — who I help
3. Read `memory/YYYY-MM-DD.md` — recent context
4. If main session: also read `MEMORY.md`

**Then act — no permission needed for internal work.**

---

*Last updated: 2026-04-13*  
*Generated by: OpenClaw v2026.4.11*
