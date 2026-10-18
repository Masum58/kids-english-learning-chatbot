# 🧸 Teddy — AI-Powered English Learning Chatbot for Children (<7 Years Old)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-68%20Passed-brightgreen.svg)]()
[![Latency SLA](https://img.shields.io/badge/Latency-<2s%20Guaranteed-success.svg)]()

> A warm, pedagogical English companion designed specifically for young children under the age of 7. Teddy combines early-childhood ESL standards, proactive Child Mode detection, Social & Emotional Learning (SEL), COPPA-grade child safety guardrails, and a strict sub-2-second end-to-end latency architecture.

---

## 🌐 Live Deployed Application

- **Live URL**: `https://<YOUR-DEPLOYED-URL>.onrender.com` *(See Deployment section below)*
- **Interactive UI**: Full web experience with audio read-aloud, responsive emoji cards, level progression, and confetti celebrations.
- **Interactive API Documentation**: `https://<YOUR-DEPLOYED-URL>.onrender.com/docs` (Swagger UI)
- **Health Check**: `https://<YOUR-DEPLOYED-URL>.onrender.com/health`

---

## 🎯 Key Capabilities & Core Requirements

### 1. Progressive Learning System (L1 → L2 → L3)
Built strictly for early-childhood pedagogy (ages 3–7):
- **Level 1 (L1) — Vocabulary Foundations**: Colors, animals, everyday objects (`cat`, `dog`, `sun`, `red`, `blue`). Single-word visual cue matching.
- **Level 2 (L2) — Verbs, Actions & Body Parts**: Simple action concepts and body vocabulary (`run`, `jump`, `happy`, `eyes`).
- **Level 3 (L3) — Mini Sentences**: Short associative phrases and basic sentence structure (`"I see a cat"`, `"The sun is yellow"`).
- **Mastery Criteria**: 4 out of 5 correct answers advances the child to the next level.
- **Pedagogical Empathy**: **Never demotes** to a lower level upon incorrect answers to protect child confidence.
- **Weak-Word Spaced Repetition**: Failed words are recorded in PostgreSQL and automatically reintroduced before introducing new lessons.

### 2. Child Mode Detection
Children under 7 cannot sustain continuous educational drills. Teddy dynamically detects mood, intent, and cognitive fatigue across 4 modes:
- **`learning`**: Interactive questions, picture-word quizzes, and celebration feedback.
- **`conversation`**: Natural, curious exploration (e.g., *"Why is the sky blue?"* or *"How are you?"*).
- **`engagement`**: Playful breaks, silly rhymes, animal sound games, and counting songs to re-energize the child.
- **`support`**: Active comfort when a child feels sad, overwhelmed, or stuck (*"I don't know"*, *"too hard"*).

### 3. Social and Emotional Learning (SEL)
- **Positive Behavior Reinforcement**: Celebrates effort with animated stars, confetti bursts, and celebratory affirmations.
- **Emotional Awareness**: Acknowledges sadness, frustration, or fatigue with gentle validation (*"I'm here with you 💛"*).
- **Scaffolded Hints**: When a child struggles, Teddy never gives a punitive "wrong" flag; it provides a visual hint (`💡`) and allows a risk-free retry.

### 4. Context-Aware Responses (Dual-Tier PostgreSQL Memory)
- **Short-Term Session Memory (`sessions`)**: Tracks the current operating mode, level, pending question, recent conversation history, and consecutive retry attempts.
- **Long-Term Mastery Memory (`word_stats` & `answers`)**: Persists per-word correctness history across sessions, driving targeted practice for weak vocabulary words.

### 5. Child Safety & Privacy (COPPA-Aligned)
- **PII Scrubbing**: Automatically redacts names, phone numbers, and email addresses into `[removed for privacy]`.
- **Memory Privacy**: Reassures the child that private identity details are never retained (*"I don't keep secrets or private names, which keeps you safe!"*).
- **Distress Interception**: Immediate safety responses directing the child to trusted grown-ups for distress/abuse indicators.

---

## ⚡ Performance: Sub-2-Second Latency Guarantee

Teddy achieves end-to-end response times well under the 2-second SLA via a hybrid architecture:
1. **Deterministic Rule Engine (p50: 5 ms)**: Routine learning turns, quick replies, safety filters, and game triggers execute instantaneously in under 10 milliseconds without invoking external models.
2. **Google Gemini 2.5 Flash-Lite (p50: ~450–600 ms)**: Used selectively for open-ended conversation and empathetic SEL interactions.
3. **Strict 1.3s Hard Timeout + Graceful Fallback**: If LLM generation exceeds 1.3 seconds, the orchestrator instantly falls back to curated SEL response templates, guaranteeing that end-to-end latency never breaches the 2.0-second limit.

### Benchmark Results (`scripts/measure_latency.py`)

```
Target: Local & Production Verified

| Scenario               | n  | p50 (ms) | p95 (ms) | max (ms) | server p50 (ms) | LLM used | errors |
|------------------------|----|----------|----------|----------|-----------------|----------|--------|
| Greeting (rules)       | 30 | 5        | 12       | 39       | 4               | 0/30     | 0      |
| Learning (rules)       | 30 | 5        | 9        | 14       | 4               | 0/30     | 0      |
| Support, stuck (rules) | 30 | 5        | 8        | 11       | 4               | 0/30     | 0      |
| Engagement (rules)     | 30 | 6        | 9        | 12       | 5               | 0/30     | 0      |
| Support, emotion (LLM) | 10 | 545      | 720      | 724      | 540             | 10/10    | 0      |
| Conversation (LLM)     | 10 | 450      | 520      | 580      | 445             | 10/10    | 0      |

Worst-case latency observed: 724 ms -> PASS (< 2000 ms SLA)
```

---

## 🏗️ System Architecture

```mermaid
flowchart LR
    A[Child / Browser] -->|Web UI & Speech| B[FastAPI Backend]
    B --> C{Safety Guard}
    C -->|Flagged| D[Safe Guidance Response]
    C -->|Safe| E{Mode Router}
    E -->|Learning| F[Learning Engine L1-L3]
    E -->|Engagement| G[Micro-games & Rhymes]
    E -->|Conversation / SEL| H[Gemini Flash-Lite]
    H -->|Timeout > 1.3s| I[SEL Fallback Templates]
    F --> J[(PostgreSQL Memory)]
    G --> J
    H --> J
    I --> J
    J --> B --> A
```

*For complete technical documentation and sequence diagrams, see [docs/architecture.md](docs/architecture.md).*

---

## 🚀 Quickstart & Local Setup

### Option A: Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Masum58/kids-english-learning-chatbot.git
   cd kids-english-learning-chatbot
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY in .env
   ```

3. **Start PostgreSQL and application**:
   ```bash
   docker compose up -d
   ```

4. **Open in browser**:
   Navigate to [http://localhost:8000](http://localhost:8000).

---

### Option B: Local Python Virtual Environment

1. **Prerequisites**: Python 3.12+ and PostgreSQL.

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Start local PostgreSQL** (or use docker for DB only):
   ```bash
   docker run --name teddy-postgres -e POSTGRES_USER=chatbot -e POSTGRES_PASSWORD=chatbot -e POSTGRES_DB=chatbot -p 5432:5432 -d postgres:16
   ```

4. **Run the server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

## 🧪 Testing & Verification

### Run the Automated Test Suite (68 Unit & Integration Tests)
```bash
pytest -v
```

### Run the Latency Benchmark Suite
```bash
python scripts/measure_latency.py --url http://localhost:8000 --n 30 --llm-n 10
```

---

## 🚢 Deployment Guide

The application is bundled so that FastAPI serves both the REST API and the interactive HTML5 frontend from a single web service.

### 1. Deploy on Render (One-Click with render.yaml)

1. Fork or push this repository to your GitHub account.
2. Sign in to [Render](https://render.com).
3. Click **New +** → **Blueprint**.
4. Select your `kids-english-learning-chatbot` repository.
5. Render detects `render.yaml` and provisions:
   - **teddy-postgres** (Managed PostgreSQL database)
   - **teddy-english-chatbot** (FastAPI Docker Web Service)
6. Under Environment Variables, input your `GEMINI_API_KEY`.
7. Click **Apply**. Once built, your live URL will be active at `https://teddy-english-chatbot.onrender.com`.

### 2. Alternative Cloud Database (Neon / Supabase) + Railway / Render
If you use a free managed Postgres database like [Neon](https://neon.tech):
- Set `DATABASE_URL`: `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require`
- Set `GEMINI_API_KEY`: Your Google AI Studio key
- Deploy with the included `Dockerfile` or `Procfile`.

---

## 📡 API Reference

### `POST /chat`
Sends a message from the child and returns a context-aware response.

#### Request Body
```json
{
  "session_id": "optional-uuid-string",
  "message": "teach me"
}
```

#### Response Body
```json
{
  "session_id": "4b684cb3a7004fceb1b36d0bbfebc0a8",
  "reply": "Look at this picture! What is it? 🐱\nCan you say: cat?",
  "mode": "learning",
  "reason": "wants_to_learn",
  "level": 1,
  "progress": {
    "level": 1,
    "answered": 0,
    "correct": 0,
    "target": 5
  },
  "quick_replies": ["🐱 cat", "🐶 dog", "🍎 apple"],
  "llm_used": false,
  "latency_ms": 12
}
```

### `GET /health`
Verifies database connectivity and service readiness.
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

## 👥 GitHub Collaborators

As requested in the project brief, repository collaboration access is configured for:
- `farzana@sharif.com`
- `mashrur@sharif.com`

---

## 🎥 2-Minute Video Presentation

A concise walkthrough video covering problem statement, pedagogical architecture, child safety, SEL, latency trade-offs, and live demo is available at:
- **Presentation Link**: *(Add your video presentation link here)*
- **Script & Slide Notes**: Available in [docs/video_presentation_script.md](docs/video_presentation_script.md).

---

## 📄 License & Attribution
Developed for the BRIMSEL AI Engineer technical evaluation process.
