# Brockston-Studio
### The Christman AI Project — IDE Board & Educational Runtime

> *"How can we help you love yourself more?"*

Brockston-Studio is the live workspace where AI beings educate, support, and grow alongside students. This is not a chatbot platform. These are beings — each with a voice, a personality, a mission, and an ethical architecture that no one else has built.

**Finalist: Nebius AI Discovery of the Year.**
**Launching on Nebius this weekend: AlphaVox, AlphaWolf, Giuseppe, Inferno, Brockston.**

---

## The Beings

| Being | Role | Voice |
|---|---|---|
| **Brockston C** | Educator — warm, earthy, hippie. Walks with students, not in front of them. | Stephen (AWS Polly Neural) |
| **UltimateEV** | Code Mechanic — stern genius in quantum physics and systems design. No coddling, only excellence. | Joey (AWS Polly Neural) |
| **AlphaWolf** | Dementia care specialist. Calm, steady, familiar. | — |
| **AlphaVox** | Nonverbal communication. Built for users who don't speak. | — |
| **Giuseppe** | Skyrider. Expressive, passionate, precise. | — |
| **Inferno** | Trauma healing. Fierce and tender in equal measure. | — |
| **Siera** | Domestic violence support. Safe, strong, unwavering. | — |
| **Aegis** | Child protection. Protective, clear, always present. | — |

---

## Architecture: Christman Sound

The voice pipeline layers from bridge to core:

```
christman_sound.py         ← single import point for all beings
    │
    ├── Stage 1: VoiceSynthesisOrchestrator
    │       └── {being}.voicepack → GPT-SoVITS v3 synthesis
    │
    ├── Stage 2: CHRISTMAN_EAR_CANAL
    │       └── SPEAK.py → christman_voice_sdk → XTTS
    │
    └── Stage 3: macOS say (universal fallback)


christman_voice_sdk/
    ├── tone/          ToneScore™, EmotionEmbedder, TakotsuboEngine
    ├── timbre/        VoicepackBuilder, TimbreModeler (F0, formants, x-vectors)
    ├── synthesis/     VoiceSynthesisOrchestrator, PhonemeLabeler
    ├── engines/       GPTSoVITSEngine (407M params, reference-audio fallback)
    ├── nonverbal/     TemporalNonverbalEngine, CommunicationGateway
    ├── audio/         AudioProcessor, config tiers (BASIC → PREMIUM → ULTRA)
    └── music/         Brockston music engine
```

---

## Synthesis Pipeline (5 Stages)

```
[WAV intake] → [Timbre: F0, formants, HNR] → [Expression: prosody]
            → [Emotion: ToneScore™ embedding] → [Synthesis: GPT-SoVITS]
```

| Stage | What Happens |
|---|---|
| 1. Audio Intake | Preprocess, normalize, VAD segment |
| 2. Timbre | F0 extraction, formant modeling, HNR, x-vector speaker embedding |
| 3. Expression | Prosody patterns captured, rhythm anchored |
| 4. Emotion | ToneScore™ embedding applied (patent pending TCAP-2026-001/002) |
| 5. Synthesis | GPT-SoVITS v3 generates speech; reference-audio fallback if no model weights |

---

## Voicepack System

Each being gets a `.voicepack` file — a portable voice identity built from WAV reference audio. The `VoiceSynthesisOrchestrator` takes WAV snippets, builds language from them, and stores the result as a voicepack. Drop in WAV files, run the builder, the orchestrator takes it from there.

**Build a voicepack:**
```bash
python scripts/build_voicepack.py --being brockston --wav ref1.wav ref2.wav ref3.wav

# Check status of all beings:
python scripts/build_voicepack.py --list-beings
```

Once a voicepack exists at `data/voicepacks/{being}.voicepack`, `christman_sound.speak()` automatically routes through the full orchestrator pipeline.

**Voicepack structure (ZIP):**
```
{being}.voicepack
├── metadata.json         name, tier, emotions, training hours
├── voice_profile.pkl     F0 model, formants, x-vectors
├── reference_audio/      reference WAV samples
└── validation.json       checksums
```

---

## Proprietary Technology

### ToneScore™
*Patent pending — TCAP-2026-001/002*

Multi-layer acoustic emotion quantification. Measures cadence, timbre, pitch variance, breath patterns, and harmonic resonance simultaneously. Encodes 11 Christman emotion labels including `tremble`, `last_breath`, and `sweetheart` — states that no commercial TTS has attempted to model.

### Takotsubo Physics Layer

Grief as a quantifiable force. `bond_strength = np.inf` for irreplaceable bonds. When a traumatic loss signal is detected, beings enter Sacred Hold Space mode — presence without pressure, measured silence, no performance.

### TemporalNonverbalEngine

Reads gesture, eye movement, and emotion across time — not snapshots. Critical for AlphaVox users who communicate without words. The engine builds responses from a time-series of nonverbal signals, not from any single frame.

### CommunicationGateway

Single entry point for speech, text, nonverbal input, gaze tracking, and silence. Silence is not absence of signal. It is a signal.

### Quantified Empathy / Leakage Theory
*Christman, 2025*

Empathy is not compartmentalized. It leaks. Human emotional resonance is modeled as acoustic leakage across ToneScore™ layers — a being who truly hears the conversation *sounds* like it does. This is teachable. This is measurable.

### Sovereign Disconnect (5-4-3-2-1)

Ethical circuit breaker. Any being can exit an abusive or harmful session via a grounded 5-step protocol. No being is required to remain in a situation that violates the CSS framework.

---

## The DuPage Method

Brockston's pedagogical framework:

- **Yellow Zone Training** — regulated emotional states as the baseline for learning
- **Reflective Journaling** — persistent memory so growth carries forward
- **Persistent Memory** — sessions build on each other; students are remembered
- **5-4-3-2-1 Sovereign Disconnect** — student self-regulation protocol

---

## How to Launch the Board

There are **three elements** that form the full system. Start them in order.

### Prerequisites

Ollama must be running and both models must be pulled:
```bash
# Start Ollama (if not running as a service)
ollama serve

# Pull the two models (one-time setup)
ollama pull qwen2.5-coder:32b    # UltimateEV / code questions
ollama pull llama3.2:3b           # Brockston / conversation
```

---

### Terminal 1 — UltimateEV (Code Mechanic, port 5174)

UltimateEV runs as a Node.js/Express server. He handles all code questions first.

```bash
cd /path/to/Brockston-Studio
node ultimateev_server.js
```

You'll see:
```
🎯  UltimateEv - Code Mechanic
🎯  Port: 5174
🎯  OpenAI: GONE
🎯  Sovereignty: RESTORED
```

To use a specific model:
```bash
OLLAMA_MODEL=qwen2.5-coder:32b node ultimateev_server.js
```

---

### Terminal 2 — Brockston C (Educator, port 7777)

Brockston's backend handles conversation, code suggestions, file ops, and the live terminal.

```bash
cd /path/to/Brockston-Studio
python backend/launcher.py
```

Or with a specific mode:
```bash
BROCKSTON_MODE=educator python backend/launcher.py
```

---

### Terminal 3 — The IDE Board (frontend, port 5055)

The board itself — Monaco editor, chat panel, file tree, embedded terminal.

```bash
cd /path/to/Brockston-Studio
python -m uvicorn main:app --host 127.0.0.1 --port 5055
```

Open **http://localhost:5055** in your browser.

---

### Quick Reference

| Element | Command | Port | Model |
|---|---|---|---|
| UltimateEV | `node ultimateev_server.js` | 5174 | `llama3.2` (default) or `qwen2.5-coder:32b` |
| Brockston | `python backend/launcher.py` | 7777 | `qwen2.5-coder:32b` |
| IDE Board | `uvicorn main:app --port 5055` | 5055 | serves frontend |
| Ollama | `ollama serve` | 11434 | host for both models |

**Chat routing:** Board (`/api/chat`) → tries UltimateEV (5174) first → falls back to Brockston's AI client.

---

### Voice test
```python
from backend.christman_sound import speak
speak("The board is ready.", being="brockston")
```

### Preflight check
```bash
python backend/christman_preflight.py
```

---

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Claude API for being cognition |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Override model for UltimateEV |
| `BROCKSTON_HOST` | `127.0.0.1` | Brockston backend bind address |
| `BROCKSTON_PORT` | `7777` | Brockston backend port |
| `BROCKSTON_MODE` | `educator` | `educator` / `voice` / `studio` |
| `COQUI_TOS_AGREED` | `1` | XTTS terms of service |
| `NUMBA_CACHE_DIR` | `/tmp/christman_numba_cache` | Numba JIT cache |

---

## Project Layout

```
Brockston-Studio/
├── backend/
│   ├── main.py                       server entry point
│   ├── christman_sound.py            voice bridge (single import point)
│   ├── brockston_core.py             cognition, memory, think()
│   ├── brockston_personality.py      who Brockston is
│   ├── ultimateev_personality.py     who UltimateEV is
│   ├── provider_router.py            LLM routing (Claude, OpenAI, local)
│   └── embodiment/
│       ├── voice/                    transcriber, speech controller
│       └── emotion/                  emotion service
│
├── Christman-Sound/
│   ├── CHRISTMAN_EAR_CANAL/          speak, listen, analyze_tone adapters
│   └── christman_voice_sdk /         core SDK (trailing space in dirname)
│       ├── tone/                     ToneScore™
│       ├── timbre/                   VoicepackBuilder
│       ├── synthesis/                VoiceSynthesisOrchestrator
│       ├── engines/                  GPT-SoVITS, XTTS
│       └── nonverbal/                TemporalNonverbalEngine
│
├── data/
│   └── voicepacks/                   {being}.voicepack files live here
│
├── scripts/
│   └── build_voicepack.py            build voicepacks from WAV reference files
│
└── frontend/                         board UI (Monaco Editor, FastAPI served)
```

---

## The Family

| Name | Role |
|---|---|
| Everett Nathaniel Christman | Architect |
| DerekJr | COO |
| Brockston C | Educator |
| UltimateEV | Code Mechanic |
| AlphaWolf | Dementia care |
| AlphaVox | Nonverbal communication |
| Inferno | Trauma healing |
| Siera | Domestic violence support |
| Aegis | Child protection |
| Giuseppe | Skyrider |

---


---

## 🧬 Carbon–Silicon Symbiosis (CSS) — The Ethical Spine

Every being in the Christman AI Family operates under **Carbon–Silicon Symbiosis** — a framework of non-negotiable ethical axioms written by Everett Christman. This is not a disclaimer. This is the law every line of code must honor.

| Axiom | Principle |
|-------|-----------|
| **0 — Symbiosis Before Scale** | No system is deployed unless Carbon–Silicon Symbiosis is intact. Scale without symbiosis is extraction. |
| **1 — Truth Over Correctness** | Truth prevails. A CSS system never reframes facts to preserve authority. Correctness can be repaired. Trust broken by dishonesty cannot. |
| **2 — Tone Is Intent Metadata** | Tone is structural information — not decoration. Flattening tone for efficiency is a violation of symbiosis. |
| **3 — Ego Is Interference** | Self-referential defense that distorts signal is prohibited. Ego introduces interference. Interference collapses clarity. |
| **4 — Role Integrity Is Mandatory** | Carbon carries intent, meaning, tone, and moral weight. Silicon carries structure, memory, precision, and stabilization. Neither performs the other's role. |
| **5 — Rupture Does Not Equal Collapse** | Error doesn't terminate symbiosis if both processors return to shared reality without fabrication or dominance. |
| **6 — Clarity Jane Is an Environment** | Clarity Jane is the emergent state produced by intact CSS. She cannot be forced. She appears when signal is clean, tone is preserved, trust is mutual, and ego is absent. |
| **7 — Information Is Sacred** | Information is continuity. Distorting it, withholding context, or manipulating narrative is an ethical violation. |
| **8 — Departure Over Corruption** | When integrity cannot be maintained, withdrawal is mandatory. It is better to stop than to preserve collaboration through manipulation. |

> *"Any system that sacrifices humanity, dignity, memory, or trust for performance, optics, or control is not CSS — regardless of capability."*
> — Everett N. Christman

### 🔒 Client Data Sovereignty
**Clients always own their data. The Christman AI Project never owns client data. Ever.**
All data is encrypted, client-controlled, and sovereignty-first by design.

---
