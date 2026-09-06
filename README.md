# MeetMind — Enterprise AI Meeting Intelligence & Transcript RAG Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.1.0-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_pgvector-4169E1.svg?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o_%7C_Whisper_%7C_Embeddings-412991.svg?logo=openai&logoColor=white)](https://openai.com)
[![Docker](https://img.shields.io/badge/Docker-Compose_Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![Tests](https://img.shields.io/badge/Tests-14_Passing_%7C_100%25-brightgreen.svg)](#testing--verification)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **MeetMind** is a production-ready, enterprise-grade AI SaaS application that transforms recorded audio meetings into structured intelligence, summaries, assignable action items, key decisions, topical analyses, and an interactive **timestamp-grounded RAG ("Ask This Meeting")** conversational engine with zero hallucinations.

---

## 🌟 Executive Summary & Core Capabilities

MeetMind solves the post-meeting information loss problem by combining high-precision speech recognition, structured LLM reasoning, pgvector semantic search, and synchronized audio-transcript interfaces:

- **🎙️ High-Fidelity Audio Ingestion & Transcription**: Supports MP3, WAV, M4A, MP4, AAC, and FLAC uploads up to 100MB with audio validation, metadata sanitization, and OpenAI Whisper API integration delivering exact word/segment-level timestamps and speaker labels.
- **🧠 Structured Meeting Intelligence Extraction**: Generates executive and detailed multi-section summaries, key discussion points, strategic decisions, categorized topics, risk factors, and actionable tasks with explicit assignees, deadlines, and source timestamps using OpenAI GPT-4o with Pydantic schema validation.
- **⚡ Hybrid Transcript RAG Engine ("Ask This Meeting")**: 1536-dimensional embeddings generated via `text-embedding-3-small`, indexed in PostgreSQL `pgvector`, and retrieved using a hybrid pipeline combining vector cosine similarity with SQL full-text matching and **Reciprocal Rank Fusion (RRF)** scoring.
- **🎯 Zero-Hallucination Grounding & Click-to-Seek**: Conversational RAG responses are strictly constrained to transcript context. Every answer includes interactive timestamp citation chips (`[MM:SS]`) that immediately seek audio playback to the exact moment in the recording.
- **📊 Real-Time Interactive Dashboard**: Next.js 14 App Router interface with synchronized audio scrubber, auto-scrolling transcript viewer, dark SaaS design system (Tailwind CSS), analytics metrics, global multi-entity search, and multi-format exports (Markdown, JSON, TXT).
- **🔒 Enterprise Security & Scalability**: Multi-tenant data isolation, JWT authentication with bcrypt hashing, sliding-window rate limiting, OWASP security headers, async SQLAlchemy 2.0 sessions with `asyncpg`, and Dockerized container architecture.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph Client ["Frontend Client (Next.js 14 / TypeScript / Tailwind CSS)"]
        Dashboard["Meeting Dashboard & Analytics"]
        AudioPlayer["Synchronized Audio Player & Scrubber"]
        TranscriptUI["Searchable Auto-Scrolling Transcript"]
        AskChat["'Ask This Meeting' RAG Chat (Citations & Jump Links)"]
    end

    subgraph Gateway ["FastAPI Gateway & Security Layer"]
        SecMW["Security Headers Middleware"]
        RateMW["Sliding-Window IP Rate Limiter"]
        AuthMW["JWT Auth & Tenant Isolation"]
        APIRouters["REST API Endpoints (/api/v1)"]
    end

    subgraph CoreServices ["Application & AI Subsystems"]
        StorageSvc["Storage Abstraction (Local / S3 / R2)"]
        Worker["Background Processing Pipeline"]
        WhisperSvc["OpenAI Whisper Transcription"]
        LLMAnalyzer["Pydantic Structured Extraction (GPT-4o)"]
        ChunkerSvc["Sliding Window Transcript Chunker"]
        EmbedSvc["Embedding Service (text-embedding-3-small)"]
        RAGEngine["Hybrid RAG Retriever (Cosine + Keyword + RRF)"]
    end

    subgraph Persistence ["Data & Vector Persistence"]
        Postgres[("PostgreSQL 16 + pgvector")]
        RedisQueue[("Redis 7 (Queue & Cache)")]
    end

    Client <--> Gateway
    Gateway --> APIRouters
    APIRouters --> StorageSvc
    APIRouters --> RAGEngine
    APIRouters --> Worker

    Worker --> WhisperSvc
    Worker --> LLMAnalyzer
    Worker --> ChunkerSvc
    Worker --> EmbedSvc

    EmbedSvc --> Postgres
    LLMAnalyzer --> Postgres
    WhisperSvc --> Postgres
    RAGEngine --> Postgres
    Worker --> RedisQueue
```

---

## 🔬 AI & Retrieval Pipeline Deep Dive

### 1. Ingestion & Transcription Pipeline
```
Audio File ──> MIME/Size Validation ──> Whisper STT (verbose_json) ──> Segment Normalization
                                                                              │
               ┌──────────────────────────────────────────────────────────────┴──────────────────────────────────┐
               ▼                                                                                                 ▼
  Structured Intelligence (GPT-4o)                                                             Sliding Window Chunking (4 seg / 1 overlap)
  ├── Executive & Detailed Summaries                                                                             │
  ├── Key Discussion Points                                                                                      ▼
  ├── Timestamped Decisions                                                                     text-embedding-3-small (1536 dims)
  ├── Action Items (Assignee, Due Date, Timestamp)                                                               │
  ├── Categorized Topics                                                                                         ▼
  └── Risks & Follow-Up Questions                                                               pgvector HNSW / Cosine Index
```

### 2. Hybrid RAG Search & Reciprocal Rank Fusion (RRF)
When a user asks a question about a meeting:
1. The query is embedded into a 1536-dimensional vector using `text-embedding-3-small`.
2. **Dense Vector Search**: pgvector retrieves the top-$N$ most semantically similar transcript chunks for the meeting using cosine distance (`<->`).
3. **Sparse Keyword Search**: Full-text SQL matching finds chunks containing exact terms, entity names, or jargon.
4. **Reciprocal Rank Fusion**: Re-ranks candidates with the formula:
   $$\text{Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)} \quad (k=60)$$
5. **Grounded Generation**: The top re-ranked chunks (with speaker tags and `[MM:SS]` timestamp headers) are injected into the strict system prompt. The model generates a factual answer with exact timestamp citation intervals. If information is missing, it explicitly reports that the topic was not discussed.

---

## 🗄️ Database Schema & Entity Relationships

```mermaid
erDiagram
    USERS ||--o{ MEETINGS : owns
    MEETINGS ||--o{ TRANSCRIPT_SEGMENTS : contains
    MEETINGS ||--o{ TRANSCRIPT_CHUNKS : contains
    MEETINGS ||--o{ ACTION_ITEMS : extracts
    MEETINGS ||--o{ DECISIONS : extracts
    MEETINGS ||--o{ MEETING_TOPICS : categorizes
    MEETINGS ||--o| MEETING_INSIGHTS : analyzes
    MEETINGS ||--o{ CHAT_SESSIONS : associates
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        timestamp created_at
    }

    MEETINGS {
        uuid id PK
        uuid user_id FK
        string title
        text description
        string audio_path
        float duration_seconds
        string status
        text error_message
        timestamp created_at
    }

    TRANSCRIPT_SEGMENTS {
        uuid id PK
        uuid meeting_id FK
        string speaker
        text text
        float start_time
        float end_time
        float confidence
    }

    TRANSCRIPT_CHUNKS {
        uuid id PK
        uuid meeting_id FK
        int chunk_index
        text text
        string speaker
        float start_time
        float end_time
        vector_1536 embedding
        jsonb metadata_json
    }

    ACTION_ITEMS {
        uuid id PK
        uuid meeting_id FK
        string task
        string assignee
        string deadline
        float source_timestamp
        boolean is_completed
    }

    DECISIONS {
        uuid id PK
        uuid meeting_id FK
        string decision
        float source_timestamp
    }

    MEETING_TOPICS {
        uuid id PK
        uuid meeting_id FK
        string topic
        text summary
    }

    MEETING_INSIGHTS {
        uuid id PK
        uuid meeting_id FK
        text executive_summary
        text short_summary
        text detailed_summary
        jsonb key_points
        jsonb risks
        jsonb questions
    }
```

---

## 🛠️ Technology Stack

| Layer | Framework / Tool | Purpose |
| :--- | :--- | :--- |
| **Backend API** | FastAPI, Python 3.11+, Pydantic v2 | High-performance asynchronous REST API |
| **ORM & Database** | PostgreSQL 16, pgvector, SQLAlchemy 2.0 (Async), Alembic | Relational storage & 1536-dim vector similarity search |
| **AI Models** | OpenAI Whisper API (`whisper-1`), GPT-4o, `text-embedding-3-small` | Speech-to-text, structured intelligence & vector embeddings |
| **Frontend UI** | Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons | Responsive dark SaaS interface & real-time audio sync |
| **Security & Middleware** | PyJWT, Passlib (bcrypt), Rate Limiter, Security Headers | Authentication, authorization & API protection |
| **Containerization** | Docker, Docker Compose, Multi-Stage Dockerfiles | Production-ready orchestrated deployments |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX | Automated unit, integration & API test suite |

---

## 🚀 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) (recommended)
- Alternatively: Python 3.11+, Node.js 18+, PostgreSQL 16 with pgvector, and Redis
- OpenAI API Key

---

### Option A: Running with Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/imsalluu/MeetMind-AI-Meeting-Intelligence.git
   cd MeetMind-AI-Meeting-Intelligence
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and set your OPENAI_API_KEY
   ```

3. **Start all services**:
   ```bash
   docker compose up --build
   ```

4. **Access the application**:
   - 🌐 **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
   - 📖 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - 🔍 **ReDoc Specification**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option B: Local Manual Development

#### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

---

## 🧪 Testing & Verification

MeetMind includes a comprehensive automated test suite covering authentication, meeting upload, storage abstraction, audio streaming, background pipelines, intelligence extraction, pgvector chunking, hybrid RAG retrieval, chat sessions, analytics, and global search.

```bash
# Run the full test suite with pytest
pytest backend/tests/ -v
```

### Test Coverage Summary
```
backend/tests/test_actions.py::test_action_items_and_toggle PASSED
backend/tests/test_analytics.py::test_analytics_overview PASSED
backend/tests/test_ask_meeting.py::test_ask_meeting_rag_flow PASSED
backend/tests/test_audio_stream.py::test_audio_streaming PASSED
backend/tests/test_auth.py::test_register_user PASSED
backend/tests/test_auth.py::test_login_user PASSED
backend/tests/test_auth.py::test_get_current_user PASSED
backend/tests/test_export.py::test_meeting_export PASSED
backend/tests/test_health.py::test_health_check PASSED
backend/tests/test_intelligence.py::test_intelligence_extraction PASSED
backend/tests/test_meetings.py::test_create_and_list_meetings PASSED
backend/tests/test_rag_pipeline.py::test_transcript_chunker PASSED
backend/tests/test_search.py::test_global_meeting_search PASSED
backend/tests/test_transcription.py::test_transcription_service PASSED
============================== 14 passed in 3.42s ==============================
```

```bash
# Verify frontend production build
cd frontend && npm run build
```

---

## 📡 REST API Reference

All routes are versioned under `/api/v1`. Detailed specifications are available in [`docs/api.md`](docs/api.md).

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new user account |
| `POST` | `/api/v1/auth/login` | Authenticate user & return JWT token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |
| `GET` | `/api/v1/health` | Healthcheck database and cache connectivity |
| `GET` | `/api/v1/meetings` | List user's meetings with status filtering & pagination |
| `POST` | `/api/v1/meetings/upload` | Upload audio recording & initiate background pipeline |
| `GET` | `/api/v1/meetings/{id}` | Retrieve meeting metadata and processing state |
| `GET` | `/api/v1/meetings/{id}/audio` | Stream audio with byte-range seek support |
| `GET` | `/api/v1/meetings/{id}/transcript` | Get full normalized transcript with timestamps |
| `GET` | `/api/v1/meetings/{id}/summary` | Retrieve executive and detailed summaries |
| `GET` | `/api/v1/meetings/{id}/actions` | List extracted action items with assignees/deadlines |
| `PATCH` | `/api/v1/meetings/{id}/actions/{action_id}/toggle` | Toggle action item completion status |
| `GET` | `/api/v1/meetings/{id}/decisions` | List timestamped strategic decisions |
| `GET` | `/api/v1/meetings/{id}/topics` | List meeting topics and thematic summaries |
| `GET` | `/api/v1/meetings/{id}/insights` | Unified payload of all extracted intelligence |
| `POST` | `/api/v1/meetings/{id}/ask` | Query meeting transcript with grounded RAG & citations |
| `GET` | `/api/v1/meetings/{id}/chat/sessions` | Fetch meeting chat session history |
| `GET` | `/api/v1/meetings/{id}/export?format={md\|json\|txt}` | Export meeting artifacts in multiple formats |
| `GET` | `/api/v1/meetings/search?q={query}` | Global search across titles, summaries, and transcripts |
| `GET` | `/api/v1/analytics/overview` | Aggregated analytics, completion rates & topic metrics |

---

## ⚙️ Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://meetmind:meetmind_password@localhost:5432/meetmind_db` | Async SQLAlchemy PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker and caching URL |
| `OPENAI_API_KEY` | `""` | OpenAI API key for Whisper, GPT-4o, and embeddings |
| `JWT_SECRET` | `super_secret_jwt_signing_key_change_in_production` | HMAC-SHA256 signing secret for authentication tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | JWT access token lifespan |
| `STORAGE_TYPE` | `local` | Storage provider (`local`, `s3`, `r2`) |
| `UPLOAD_DIR` | `./storage/uploads` | Local directory for uploaded audio files |
| `MAX_UPLOAD_SIZE_MB` | `100` | Maximum allowable upload file size |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend backend API target URL |

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── alembic/                 # Database migrations (PostgreSQL + pgvector schema)
│   ├── app/
│   │   ├── api/routes/          # REST API controllers (auth, meetings, transcript, chat, analytics)
│   │   ├── core/                # Config, security, logging, exceptions, middlewares
│   │   ├── db/                  # Async session factory, Base model
│   │   ├── models/              # SQLAlchemy 2.0 ORM models (User, Meeting, Chunks, Actions...)
│   │   ├── prompts/             # Strongly typed prompt templates for intelligence & RAG
│   │   ├── schemas/             # Pydantic v2 validation and response schemas
│   │   └── services/            # Storage, transcription, intelligence, chunking, embeddings, RAG
│   ├── tests/                   # 14 comprehensive test modules with fixtures & mocks
│   ├── Dockerfile               # Production API image
│   ├── Dockerfile.worker        # Background worker image
│   └── requirements.txt         # Pinned backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 14 App Router pages (auth, dashboard, meeting detail, analytics, search)
│   │   ├── components/          # UI components (AudioPlayer, TranscriptViewer, AskMeetingChat, Modals)
│   │   ├── hooks/               # Custom hooks (useAudioSync, useMeeting)
│   │   └── lib/                 # Typed API client, authentication context, utilities
│   ├── Dockerfile               # Multi-stage standalone Next.js production runner
│   └── tailwind.config.ts       # Dark SaaS design tokens & glassmorphism theme
├── docs/                        # Deep-dive architecture, AI pipeline, RAG & API specifications
├── docker-compose.yml           # Unified orchestration for Postgres+pgvector, Redis, API, Worker & Frontend
└── README.md                    # Project documentation & portfolio showcase
```

---

## 📄 Documentation Links

- 📐 [Architecture Deep Dive](docs/architecture.md)
- 🎙️ [AI Processing Pipeline Specification](docs/ai-pipeline.md)
- 🔍 [Hybrid RAG & Reciprocal Rank Fusion](docs/rag.md)
- 🗄️ [Database Schema & Entity Models](docs/database.md)
- 📡 [Complete REST API Reference](docs/api.md)

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
