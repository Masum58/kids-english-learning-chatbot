# 2-Minute Video Presentation Script (English Only)

**Target Duration**: 1 minute 55 seconds (~240 words spoken at a clear, natural pace of ~125 wpm)  
**Topic**: Design Decisions, Tools, Technology Choices & Trade-Offs for Teddy English Chatbot  

---

## ⏱️ Video Timeline & Teleprompter Script

### [0:00 – 0:25] Introduction & The Core Problem
**Visual**: Show project title, Teddy hero banner, and age target badge `<7 Years Old`.

> "Hello! Today, I’m presenting **Teddy**, an AI-powered conversational English learning platform built specifically for young children under seven.  
> Teaching toddlers and preschoolers presents unique engineering challenges: young kids have short attention spans, fragile emotional confidence, and distinct safety requirements. Continuous drill-based quizzes lead to cognitive fatigue, which is why a traditional chatbot approach doesn't work."

---

### [0:25 – 0:55] Architecture & Technology Choices
**Visual**: Display the Architecture Diagram ([docs/architecture.md](architecture.md)) and show the tech stack icons (FastAPI, PostgreSQL, Gemini Flash-Lite).

> "To solve this, we architected Teddy using **FastAPI** for high-throughput asynchronous request handling, connected to **PostgreSQL** for dual-tier memory.  
> Short-term state tracks the child’s active lesson and sliding-window context, while long-term relational tables record vocabulary mastery and identify weak words for spaced repetition.  
> For intelligence, we selected **Google Gemini 2.5 Flash-Lite** because of its fast time-to-first-token and reliable tone steering."

---

### [0:55 – 1:25] Child Modes, SEL & Safety Guardrails
**Visual**: Live interface demo: click "📚 Learn", transition to "I'm sad" (support mode), show celebratory stars and confetti.

> "Teddy implements four dynamic **Child Modes**: **Learning** across Levels 1 to 3, casual **Conversation**, playful **Engagement** with rhymes and games, and emotional **Support**.  
> In line with early-childhood Social and Emotional Learning (SEL), Teddy **never demotes** a child upon mistakes. Instead, it provides gentle scaffolded hints.  
> Safety is built directly into the kernel: all personally identifiable information like names and numbers is scrubbed before processing, and distress cues immediately trigger protective adult guidance."

---

### [1:25 – 1:55] The 2-Second Latency Trade-Off & Fallback
**Visual**: Show `scripts/measure_latency.py` terminal output showing p50: 5ms rule path, 545ms LLM path, max 724ms.

> "A non-negotiable requirement was a **sub-2-second end-to-end response latency**.  
> The trade-off: large LLMs are expressive but unpredictable in latency. We solved this with a **hybrid deterministic-LLM architecture**:  
> Routine lesson validations and safety checks execute via our deterministic rule engine in under **10 milliseconds**.  
> When the LLM is invoked, an asynchronous **1.3-second hard deadline** is enforced. If the model is slow or rate-limited, Teddy gracefully falls back to pre-curated SEL templates in under a millisecond, guaranteeing our latency SLA is never breached."

---

### [1:55 – 2:00] Conclusion
**Visual**: Show the live deployed URL on Render/Railway.

> "The system is fully containerized with Docker and live in production. Thank you for your time, and I look forward to your feedback!"

---

## 🎬 Recording & Presentation Tips
1. **Screen Layout**: Split screen with the browser on the left ([http://localhost:8000](http://localhost:8000) or Live URL) and terminal/diagrams on the right.
2. **Audio**: Speak with warm, upbeat clarity.
3. **Demo Action**:
   - Type `"teach me"` -> Teddy shows animal picture question with choices.
   - Click answer -> Confetti burst and star earned!
   - Type `"I am sad"` -> Teddy shifts to supportive, comforting SEL mode.
