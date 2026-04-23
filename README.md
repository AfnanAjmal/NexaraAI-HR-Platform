# NexaraAI — Agentic HR Interview Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?style=for-the-badge&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-purple?style=for-the-badge)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-darkgreen?style=for-the-badge&logo=mongodb)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-orange?style=for-the-badge)

**A production-grade Agentic AI system that automates the entire HR interview pipeline — from candidate ingestion to AI-conducted voice interviews and automated evaluation.**

</div>

---

## Table of Contents

- [Overview](#overview)
- [System Modes](#system-modes)
- [Architecture](#architecture)
- [LangGraph Flows](#langgraph-flows)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Installation & Setup](#installation--setup)
- [How to Run](#how-to-run)
- [Interview Flow (End-to-End)](#interview-flow-end-to-end)
- [Database Design](#database-design)

---

## Overview

NexaraAI is a dual-mode AI platform:

1. **Normal Mode** — A RAG-powered chatbot that answers questions about the company, services, and policies using ChromaDB vector search and Groq LLM.

2. **HR Mode** — A complete, end-to-end HR automation system. HR staff can add candidates, the system extracts resume/JD info, generates a structured interview plan, sends email invitations, conducts a fully automated AI voice interview using Deepgram STT + ElevenLabs TTS, evaluates performance, and sends offer or rejection emails — all without human involvement.

---

## System Modes

### 🔵 Normal Mode (RAG Chatbot)

- Default mode for all users
- Powered by ChromaDB + HuggingFace embeddings
- Answers company-related questions from ingested documents
- Uses `llama-3.1-8b-instant` via Groq for generation

### 🔴 HR Mode (Hidden Feature)

- Activated by typing `#hr:1234` in the chat
- Only accessible to authorized HR staff
- Full candidate management pipeline
- Triggers interview automation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                       │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐   │
│  │ /chat    │  │ /hr      │  │ /interview             │   │
│  │ router   │  │ router   │  │ router                 │   │
│  └────┬─────┘  └────┬─────┘  └────────────┬───────────┘   │
│       │              │                      │               │
│  ┌────▼─────┐  ┌────▼──────────────┐  ┌───▼────────────┐  │
│  │ Chat     │  │ Candidate         │  │ Interview      │  │
│  │ LangGraph│  │ Pipeline          │  │ LangGraph      │  │
│  │ (RAG +   │  │ (Extract→Plan→    │  │ (8-node agent) │  │
│  │  HR mode)│  │  Save→Email)      │  │                │  │
│  └────┬─────┘  └────┬──────────────┘  └───┬────────────┘  │
│       │              │                      │               │
│  ┌────▼─────────────▼──────────────────────▼────────────┐  │
│  │              Services Layer                           │  │
│  │  RAG | Extraction | ElevenLabs | Deepgram | Email    │  │
│  └────┬──────────────────────────────────────────────────┘  │
│       │                                                     │
│  ┌────▼──────────────┐   ┌─────────────────────────────┐  │
│  │  ChromaDB         │   │  MongoDB Atlas              │  │
│  │  (Vector Store)   │   │  (Candidates + Interviews)  │  │
│  └───────────────────┘   └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## LangGraph Flows

### Chat Graph

```
__start__
    │
    ▼
mode_selection
    │
    ├── normal ──► normal_rag_answer ──► __end__
    │
    └── hr ──────► hr_handler ──────────► __end__
```

The `mode_selection` node checks if the user is authenticated in HR mode. Normal queries go through the full RAG pipeline. HR messages are handled by the HR state machine (menu → collect email → collect JD → collect resume → background processing).

### Interview Graph

```
__start__
    │
    ├── (empty input) ──► ask_question ──────────────────────► __end__
    │
    └── (has input) ───► input_router_node
                              │
                ┌─────────────┼──────────────────┬──────────────┐
                │             │                  │              │
                ▼             ▼                  ▼              ▼
        silence_handler  repeat_question  company_rag_answer  normal_interview_flow
                │             │                  │              │
                │             │                  │         (FOLLOWUP → stay)
                │             │                  │         (ACK → next phase)
                │             │                  │              │
                └─────────────┴──────────────────┴──────────────┤
                                                                 │
                                              candidate_questions_handler
                                                      │
                                              (no) ───► evaluate → done
                                              (question) ─► RAG answer
                                                           → "Any other questions?"
                                                   │
                                                __end__
```

**Key routing logic:**
- Empty input → `ask_question` (re-states current question)
- `"repeat"` / `"again"` / `"rephrase"` → `repeat_question`
- Company question with `?` and Nexara keywords → `company_rag_answer`
- All other answers → `normal_interview_flow`
- `phase == "candidate_questions"` → `candidate_questions_handler`

**Smart follow-up detection in `normal_interview_flow`:**
```
Answer evaluation:
  - Empty / 1-2 meaningless words (ok, yes, fine) → FOLLOWUP: ask for more detail
  - Any real answer, even brief              → ACK: acknowledge + advance phase
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend Framework | FastAPI | REST API, routing, static files |
| Agentic Orchestration | LangGraph | Stateful interview & chat flows |
| LLM | Groq (`llama-3.1-8b-instant`) | Generation, extraction, evaluation |
| Embeddings | HuggingFace (`BAAI/bge-small-en-v1.5`) | Document embeddings |
| Vector Database | ChromaDB | RAG document retrieval |
| Document Database | MongoDB Atlas | Candidates & interview data |
| Speech-to-Text | Deepgram (nova-2) | Real-time voice transcription |
| Text-to-Speech | ElevenLabs (`eleven_turbo_v2_5`) | Sarah's voice responses |
| Email | Resend API | Interview invites, offer & rejection letters |
| Frontend | HTML / CSS / JavaScript | Chat UI, HR dashboard, interview page |
| PDF Parsing | PyMuPDF (fitz) | Resume text extraction |
| State Persistence | LangGraph MemorySaver | In-memory session checkpointing |

---

## Project Structure

```
Agent_Project/
│
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Centralized environment config
│   │
│   ├── database/
│   │   ├── mongo.py               # MongoDB Atlas (motor async client)
│   │   └── chroma.py              # ChromaDB vector store + retriever
│   │
│   ├── graph/
│   │   ├── state.py               # TypedDict state definitions
│   │   ├── chat_graph.py          # Chat LangGraph (RAG + HR mode)
│   │   └── interview_graph.py     # Interview LangGraph (8 nodes)
│   │
│   ├── models/
│   │   └── schemas.py             # Pydantic models for API & LLM output
│   │
│   ├── routers/
│   │   ├── chat.py                # POST /chat
│   │   ├── hr.py                  # POST /upload_resume, GET /candidates
│   │   └── interview.py           # GET+POST /interview/*
│   │
│   └── services/
│       ├── rag.py                 # RAG pipeline (ChromaDB → LLM)
│       ├── extraction.py          # Resume & JD structured extraction
│       ├── interview_plan.py      # LLM interview question generation
│       ├── evaluation.py          # Post-interview scoring (LLM)
│       ├── email_service.py       # Resend: invite, offer, rejection
│       ├── elevenlabs_service.py  # TTS: text → mp3 bytes
│       ├── did_service.py         # D-ID lip-sync (unused after pivot)
│       └── token_service.py       # Secure interview link token gen
│
├── frontend/
│   ├── index.html                 # Normal chat + HR mode UI
│   ├── hr_dashboard.html          # HR candidate pipeline dashboard
│   ├── interview.html             # Voice interview page (Zoom-style)
│   └── static/
│       └── sarah.jpg              # AI interviewer avatar photo
│
├── data/                          # Source PDFs for ChromaDB ingestion
├── ingest.py                      # Run once: ingest PDFs into ChromaDB
├── graph.py                       # Visualize graphs → PNG output
├── requirements.txt
├── .env.example
└── README.md
```

---

## Features

### Candidate Pipeline (HR Mode)
- HR activates mode via secret passcode (`#hr:1234`)
- Upload candidate **Resume (PDF)** and paste **Job Description**
- LLM extracts structured info: name, email, skills, experience, role, level
- Auto-generates **structured interview plan** (intro + technical + behavioral questions)
- Saves candidate to **MongoDB Atlas** with `status: pending`
- Generates unique **secure interview token**
- Sends **interview invitation email** via Resend with a direct link

### AI Voice Interview
- Candidate opens unique link → Zoom-style dark video call page
- **Sarah** (AI interviewer) greets candidate using ElevenLabs voice
- Fully automatic voice conversation loop:
  ```
  Sarah speaks → audio ends → mic opens → Deepgram STT →
  transcript → LangGraph → response → ElevenLabs TTS →
  audio plays → repeat
  ```
- Smart answer detection: short/vague → follow-up question; good → advance
- Company questions answered live via RAG mid-interview
- Q&A phase at the end: candidate can ask anything about the role/company
- Saying "no" to Q&A ends the interview → silent evaluation

### Evaluation & Outcome
- LLM evaluates full conversation transcript
- Scores: Technical, Communication, Confidence, Overall (0–10 each)
- Scores stored in MongoDB, **never shown** to the candidate
- If `overall >= threshold (7.0)` → `status: selected` → **offer letter email**
- Else → `status: rejected` → **rejection email**

### RAG Chatbot
- Ingests company PDF documents into ChromaDB once via `ingest.py`
- `BAAI/bge-small-en-v1.5` embeddings for semantic similarity
- Top-k chunk retrieval → Groq LLM for answer synthesis

---

## API Endpoints

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message (normal RAG or HR mode) |

### HR
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/hr/process_candidate` | Upload resume PDF + JD text |
| `GET`  | `/candidates` | Get all candidates with status |

### Interview
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/interview/config?token=` | Returns Deepgram API key (token-gated) |
| `GET`  | `/interview/{token}` | Serve the interview HTML page |
| `POST` | `/interview/start` | Initialize LangGraph, get first question |
| `POST` | `/interview/respond` | Text-based response (original endpoint) |
| `POST` | `/interview/speak` | Text → ElevenLabs audio (base64 mp3) |
| `POST` | `/interview/answer` | STT text → LangGraph → audio response |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values:

```env
# LLM
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=llama-3.1-8b-instant

# Embeddings
EMBED_MODEL=BAAI/bge-small-en-v1.5

# Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=nexaraai
CHROMA_DIR=./chroma-db

# App
BASE_URL=http://localhost:8000
HR_PASSCODE=1234
SCORE_THRESHOLD=7.0

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=onboarding@resend.dev
RESEND_TO_OVERRIDE=your_email@gmail.com   # dev mode: redirect all emails here
CONTACT_EMAIL=hr@nexaraai.com

# Voice (Deepgram STT)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Voice (ElevenLabs TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL

# Avatar photo URL (must be publicly accessible for D-ID)
SARAH_PHOTO_URL=http://localhost:8000/static/sarah.jpg
```

> **Note for local dev:** Deepgram requires a real microphone. ElevenLabs free tier uses `eleven_turbo_v2_5` model only.

---

## Installation & Setup

### Prerequisites
- Python 3.12+
- MongoDB Atlas account (free tier works)
- Groq API key (free)
- Resend API key (free)
- Deepgram API key (free tier)
- ElevenLabs API key (free tier)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/AfnanAjmal/NexaraAI-HR-Platform.git
cd NexaraAI-HR-Platform

# 2. Create and activate virtual environment
python -m venv env-agent
source env-agent/bin/activate      # macOS/Linux
# env-agent\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Ingest company documents into ChromaDB
# Place your PDF files in the data/ folder first
python ingest.py

# 6. (Optional) Visualize LangGraph flows
python graph.py
# Opens chat_graph.png and interview_graph.png
```

---

## How to Run

```bash
# Start the FastAPI server
uvicorn backend.main:app --reload
```

Open your browser:
- **Chat Interface:** `http://localhost:8000`
- **HR Dashboard:** `http://localhost:8000/hr/dashboard`
- **Interview Page:** sent via email to candidate as `http://localhost:8000/interview/{token}`

---

## Interview Flow (End-to-End)

```
HR Staff                     System                        Candidate
   │                            │                              │
   ├─ Types #hr:1234 ──────────►│                              │
   ├─ Selects "New Candidate" ──►│                              │
   ├─ Pastes JD ────────────────►│                              │
   ├─ Pastes Resume ────────────►│                              │
   │                            ├─ Extract info (LLM) ─────────│
   │                            ├─ Generate interview plan ─────│
   │                            ├─ Save to MongoDB ─────────────│
   │                            ├─ Send invite email ──────────►│
   │                            │                              │
   │                            │         ┌────────────────────┤
   │                            │         │ Opens interview link│
   │                            │◄────────┤ Clicks Start        │
   │                            ├─ Greeting (ElevenLabs) ──────►│
   │                            ├─ Ask intro question ─────────►│
   │                            │◄──── Voice answer (Deepgram) ─┤
   │                            ├─ Acknowledge + ask technical ►│
   │                            │◄──── Voice answer ────────────┤
   │                            ├─ Acknowledge + ask behavioral ►│
   │                            │◄──── Voice answer ────────────┤
   │                            ├─ "Do you have any questions?" ►│
   │                            │◄──── "No, that's all" ─────────┤
   │                            ├─ Evaluate (silent) ────────────│
   │                            ├─ Update MongoDB status ────────│
   │                            ├─ Send offer/rejection email ──►│
   │                            │                              │
```

---

## Database Design

### MongoDB — `candidates` collection
```json
{
  "id": "uuid",
  "name": "Afnan Ajmal",
  "email": "candidate@email.com",
  "resume_text": "...",
  "jd_text": "...",
  "resume_info": { "skills": [], "experience": "...", "education": "..." },
  "jd_info": { "role": "Junior Python Developer", "required_skills": [] },
  "interview_plan": {
    "intro": ["Tell me about yourself..."],
    "technical": ["Explain how a REST API works..."],
    "behavioral": ["Tell me about a challenge you faced..."]
  },
  "token": "secure_hex_token",
  "status": "pending | interviewed | selected | rejected",
  "score": 8.5,
  "evaluation": {
    "technical_score": 8,
    "communication": 9,
    "confidence": 8,
    "overall": 8.5,
    "summary": "..."
  }
}
```

### ChromaDB — company documents
```
Collection: company_docs
Documents: chunked text from PDFs in data/
Embeddings: BAAI/bge-small-en-v1.5 (384-dim)
Metadata: source filename, chunk index
```

---

## Graph Visualizations

Run `python graph.py` to regenerate these diagrams.

### Chat Graph
![Chat Graph](chat_graph.png)

### Interview Graph
![Interview Graph](interview_graph.png)

---

## Author

**Afnan Ajmal**
- GitHub: [@AfnanAjmal](https://github.com/AfnanAjmal)
- LinkedIn: [linkedin.com/in/afnan-ajmal](https://linkedin.com/in/afnan-ajmal)
- Email: afnanajmal03@gmail.com

---

<div align="center">
Built with LangGraph · FastAPI · Groq · ChromaDB · MongoDB · Deepgram · ElevenLabs
</div>
