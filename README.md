# MeetMind — AI Meeting Intelligence

> **Production-Grade Enterprise AI Meeting Intelligence & RAG Platform**

MeetMind transforms audio recordings of meetings into structured intelligence, summaries, action items with assignees, timestamped decisions, topics, risks, and an interactive, transcript-grounded Retrieval-Augmented Generation (RAG) conversational agent.

---

## Key Features

- **Centralized AI Services**: OpenAI Whisper Speech-to-Text with segment timestamps, structured Pydantic LLM analysis, and 1536-dimensional vector embeddings.
- **Transcript-Grounded RAG ("Ask This Meeting")**: Hybrid vector search (pgvector) + PostgreSQL full-text retrieval with Reciprocal Rank Fusion, timestamp attribution, and zero-hallucination guardrails.
- **Interactive Audio Sync**: Synchronized audio playback with auto-scrolling transcript and click-to-seek timestamp citations.
- **Meeting Intelligence Extraction**: Executive summaries, detailed breakdowns, action items with assignees/deadlines, decisions, topics, and risk factors.
- **Robust Background Processing**: Asynchronous worker pipeline (`PENDING` -> `PROCESSING` -> `COMPLETED` / `FAILED`) with automatic error handling and retry mechanisms.
- **Enterprise Security**: JWT authentication, bcrypt password hashing, strict multi-tenant user data isolation, and validated file storage abstractions.
- **Modern SaaS Dashboard**: Next.js 14 App Router, TypeScript, Tailwind CSS, analytics charts, global search, and multi-format exports (Markdown, JSON, TXT).

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend API** | FastAPI, Python 3.11+, Pydantic v2, Uvicorn |
| **Database & Vector Store** | PostgreSQL 16, pgvector, SQLAlchemy 2.0 (Async), Alembic |
| **AI & LLM Services** | OpenAI Whisper API, GPT-4o Structured Outputs, text-embedding-3-small |
| **Worker / Queue** | ARQ, Redis, resilient in-process background worker |
| **Frontend App** | Next.js (App Router), TypeScript, Tailwind CSS, Lucide Icons, TanStack Query |
| **Containerization** | Docker, Docker Compose, multi-stage production builds |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX, Mock AI services |

---

## System Architecture

```
                                  +-----------------------+
                                  |   Next.js Frontend    |
                                  |  (Dashboard & Player) |
                                  +-----------+-----------+
                                              |
                                         REST / JSON
                                              |
                                  +-----------v-----------+
                                  |    FastAPI Backend    |
                                  +-----+-----+-----+-----+
                                        |     |     |
              +-------------------------+     |     +-------------------------+
              |                               |                               |
    +---------v---------+           +---------v---------+           +---------v---------+
    |    PostgreSQL     |           |   Redis Queue     |           |  Centralized AI   |
    |  - pgvector RAG   |           |  - Worker Engine  |           |  - Whisper STT    |
    |  - Relational DB  |           |  - Job Tracking   |           |  - GPT-4o LLM     |
    +-------------------+           +-------------------+           +-------------------+
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker & Docker Compose (optional for containerized run)
- OpenAI API Key

### Quick Start with Docker
```bash
cp .env.example .env
# Add your OPENAI_API_KEY in .env

docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

---

## Project Structure
```
├── backend/
│   ├── app/
│   │   ├── api/routes/        # Auth, meetings, transcript, chat, analytics
│   │   ├── core/              # Config, security, logging, exceptions
│   │   ├── db/                # Session, base models
│   │   ├── models/            # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/           # Pydantic v2 validation schemas
│   │   ├── services/          # AI services, RAG, storage, worker
│   │   └── prompts/           # Strongly typed prompt templates
│   ├── alembic/               # Database migrations
│   └── tests/                 # Comprehensive test suite
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App router pages
│   │   ├── components/        # UI, audio player, transcript, chat
│   │   ├── hooks/             # Custom React hooks
│   │   └── lib/               # API client, auth state
└── docs/                      # Technical architecture, AI pipeline & RAG specs
```

---

## License
MIT License
