# 🦞 DevClaw: Python Reference Architecture for OpenClaw

A clear, lightweight, and educational Python project demonstrating the core architectural concepts of **[OpenClaw](https://openclaw.ai/)** (*"The AI that really does things"*).

---

## 🎯 What is OpenClaw?

[OpenClaw](https://openclaw.ai/) is an open-source, self-hosted autonomous AI assistant designed to run directly on your own machine. Unlike traditional conversational chatbots that only respond with text inside a browser tab, OpenClaw:
1. **Takes Real Autonomous Actions**: Organizes inboxes, sends emails, schedules calendar events, and automates web workflows (like flight check-ins).
2. **Works Everywhere via Your Existing Chat Apps**: Connects to 20+ channels including WhatsApp, Telegram, Discord, Slack, and iMessage.
3. **Local-First & Privacy-Focused**: Your memories, credentials, preferences, and data remain strictly on your local hardware.
4. **Model Agnostic**: Compatible with Claude, Gemini, GPT, or local models via Ollama.
5. **No Subscriptions / Independent Non-Profit**: Stewarded by the OpenClaw Foundation (501(c)(3)).

---

## 🏗️ How DevClaw Maps to OpenClaw's Architecture

`devclaw` reflects OpenClaw's design in clean, readable Python with **zero external dependencies** (pure standard library):

```
                       ┌──────────────────────────────────────────────┐
                       │           Connected Chat Channels            │
                       │   (WhatsApp, Telegram, Discord, CLI Shell)   │
                       └──────────────────────┬───────────────────────┘
                                              │ (Normalized ChannelMessage)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LOCAL DEVCLAW GATEWAY                              │
│                                                                             │
│   ┌───────────────────────────┐         ┌───────────────────────────────┐   │
│   │     Autonomous Agent      │◄───────►│      Local Persistent DB      │   │
│   │    (Reasoning + Acting)   │         │           (SQLite)            │   │
│   └─────────────┬─────────────┘         │  • Memories & Preferences     │   │
│                 │                       │  • Local Calendar             │   │
│                 ▼                       │  • Local Inbox                │   │
│   ┌───────────────────────────┐         │  • Action Audit Logs          │   │
│   │     AgentSkills Engine    │         └───────────────────────────────┘   │
│   │                           │                                             │
│   │  • email_manager          │         ┌───────────────────────────────┐   │
│   │  • calendar_scheduler     │◄───────►│       Model Provider          │   │
│   │  • flight_checkin         │         │  (Mock / Gemini / OpenAI)     │   │
│   │  • local_memory           │         └───────────────────────────────┘   │
│   │  • system_status          │                                             │
│   └───────────────────────────┘                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Component | OpenClaw Concept | DevClaw Implementation |
|---|---|---|
| **Gateway Daemon** | Runs locally on your machine, managing channels & state | [`core/gateway.py`](file:///home/vinayak/Desktop/devclaw/core/gateway.py) |
| **Channel Adapters** | Normalizes messages from WhatsApp, Telegram, CLI | [`channels/`](file:///home/vinayak/Desktop/devclaw/channels/) (`cli_channel.py`, `webhook_channel.py`) |
| **Agent ReAct Loop** | Decomposes intent into tool calls and chains actions | [`core/agent.py`](file:///home/vinayak/Desktop/devclaw/core/agent.py) |
| **AgentSkills Engine** | Extensible plug-and-play tools with parameter schemas | [`skills/`](file:///home/vinayak/Desktop/devclaw/skills/) (`registry.py`, `@skill` decorator) |
| **Local Memory** | 100% private SQLite storage for facts and audit logs | [`core/memory.py`](file:///home/vinayak/Desktop/devclaw/core/memory.py) |
| **Model Provider** | Model-agnostic layer (offline smart mock + OpenAI/Gemini) | [`core/llm.py`](file:///home/vinayak/Desktop/devclaw/core/llm.py) |

---

---

## 📦 Requirements & Installation

DevClaw's core runs using the **Python Standard Library** (Python 3.10+), requiring zero mandatory external packages.

To install optional packages for local Ollama orchestration, rich terminal styling, and testing:

```bash
pip install -r requirements.txt
```

Contents of [`requirements.txt`](file:///home/vinayak/Desktop/devclaw/requirements.txt):
- `rich`: Pretty formatted terminal bubbles & tables
- `ollama`: Direct local Ollama Python client
- `openai`: OpenAI API client (optional for cloud models)
- `requests`: HTTP client utilities
- `pytest`: Automated test runner

---

## ⚡ Execution Modes

DevClaw supports multiple runtime modes depending on your workflow:

### Mode 1: Built-in Offline Reasoning (Zero-Config, Instant)
Runs completely offline with zero API keys or external daemons:

```bash
# Automated showcase tour (flight check-in, inbox triage, calendar sync)
python3 run.py --demo

# Interactive chat shell
python3 run.py

# Inspect SQLite database & registered skills
python3 run.py --status
```

### Mode 2: Local Offline LLM via Ollama (100% Private, Deep Generative AI)
Run real open-source LLMs locally on your own machine (no internet required, zero cloud leakage, zero cost):

1. **Verify your local Ollama models**:
   ```bash
   ollama list
   ```
   *(e.g., `qwen2.5:1.5b` or `llama3:latest`)*

2. **Launch DevClaw connected to Ollama**:
   ```bash
   # Default fast local model (qwen2.5:1.5b)
   python3 run.py --ollama

   # Or specify llama3:latest
   python3 run.py --ollama --model llama3:latest
   ```

Now you can ask **any arbitrary open-ended question** (coding, analysis, science, creative writing) while the agent also retains full access to local OpenClaw skills (emails, calendar, weather, memory)!

### Mode 3: Direct Integration with Real OpenClaw Engine
Directly inspect and drive the real installed OpenClaw CLI and daemon from Python:

```bash
python3 run.py --real
```

### Mode 4: Client Web Dashboard (Interactive Browser Tab)
Launch a visual, client-ready dashboard with live WhatsApp/Telegram chat simulation and real-time state inspection tabs:

```bash
# Launch with built-in engine on http://localhost:8000
python3 run.py --web

# Or launch with local Ollama LLM
python3 run.py --web --ollama
```

### Mode 5: Cloud Model Providers (Optional)
If you wish to use cloud models:
```bash
export OPENAI_API_KEY="sk-..."
python3 run.py
```

---

## 🧩 Adding a Custom AgentSkill

Adding a new skill in DevClaw follows OpenClaw's plugin philosophy: simply decorate any Python function with `@skill`:

```python
from skills.registry import skill

@skill(
    name="track_package",
    description="Look up tracking status and delivery estimate for a parcel.",
    parameters={
        "tracking_number": {"type": "string", "required": True},
        "carrier": {"type": "string", "required": False, "default": "UPS"},
    }
)
def track_package(memory, tracking_number: str, carrier: str = "UPS") -> dict:
    # Autonomous logic (API, browser automation, or local lookup)
    return {
        "status": "OUT_FOR_DELIVERY",
        "carrier": carrier,
        "tracking_number": tracking_number,
        "estimated_delivery": "Today by 4:00 PM"
    }
```

The gateway immediately registers the skill, exposes its JSON schema to the model, and logs every execution into the local audit table in `devclaw.db`.

---

## 🦞 Direct Integration with the Real OpenClaw Engine

In addition to the standalone architectural reference, DevClaw includes a direct Python bridge to the **real installed OpenClaw engine** (`openclaw_bridge.py`):

```python
from openclaw_bridge import OpenClawBridge

# Connect Python directly to the real OpenClaw engine
claw = OpenClawBridge()

# 1. Query real OpenClaw engine version
print(claw.version())  # e.g., OpenClaw 2026.6.35

# 2. Get real OpenClaw Gateway & Channel status
print(claw.status())

# 3. Inspect real bundled OpenClaw skills
weather_info = claw.get_skill_info("weather")
triage_info = claw.get_skill_info("taskflow-inbox-triage")
```

### Try it now:
```bash
# Run Python directly against real OpenClaw
python3 run.py --real
```

Inside the interactive chat (`python3 run.py`), you can also query the real OpenClaw engine anytime:
- `/real status` — Fetches live status table from the real OpenClaw daemon
- `/real skills` — Lists real bundled OpenClaw skills
- `/real skill weather` — Inspects the real weather skill manifest

---

## 🛡️ Security & Privacy Principles

1. **Zero Cloud State**: No personal facts, emails, or credentials are sent to a hosted cloud tier.
2. **Action Audit Logs**: Every autonomous action taken by the agent is recorded with parameters and status in `audit_logs` for complete transparency.
3. **Bring Your Own Model**: Switch between offline local models (via Ollama) or commercial APIs without changing application code.

