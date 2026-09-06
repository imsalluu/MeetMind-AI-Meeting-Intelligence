# MeetMind System Architecture

## Overview
MeetMind is an enterprise-grade AI Meeting Intelligence SaaS platform that converts audio recordings into structured knowledge, summaries, action items, decisions, and an interactive timestamp-grounded RAG ("Ask This Meeting") system.

```
+-----------------------------------------------------------------------------------+
|                                Next.js Frontend                                    |
|   (Dashboard, Audio Sync Player, Searchable Transcript, Ask Meeting RAG Chat)     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                    REST / JSON
                                          |
+-----------------------------------------v-----------------------------------------+
|                                FastAPI Backend                                    |
|  - JWT Authentication & Strict User Data Isolation                                |
|  - Storage Abstraction Layer (Local / S3 / R2)                                     |
|  - Async Relational Session (SQLAlchemy 2.0)                                      |
|  - Centralized AI Service Subsystem                                               |
+-------------------+---------------------+--------------------+--------------------+
                    |                     |                    |
        +-----------v-----------+  +------v------+   +---------v---------+
        | PostgreSQL + pgvector |  | Redis Queue |   |  OpenAI Services  |
        |  - Relational Models  |  |  - ARQ /    |   |  - Whisper STT    |
        |  - Vector Embeddings  |  |    Worker   |   |  - text-embed-3-sm|
        |  - Full-Text Search   |  +------+------+   |  - GPT-4o JSON    |
        +-----------------------+         |          +-------------------+
                                          |
                               +----------v----------+
                               | Background Worker   |
                               |  - Transcribe       |
                               |  - Extract Insights |
                               |  - Generate Chunks  |
                               |  - Index Embeddings |
                               +---------------------+
```

## Key Architectural Principles

1. **Clean Separation of Concerns**:
   - Routes only handle HTTP validation and response formatting.
   - Business logic resides in `services/`.
   - Data access resides in SQLAlchemy repositories and models.
   - Centralized AI operations are encapsulated in `services/ai/`.

2. **Strict User Isolation**:
   - All queries filter by `user_id` derived from the validated JWT token.
   - Meeting ownership is enforced at the dependency/service layer before any operation.

3. **Asynchronous Non-Blocking Processing**:
   - File uploads return immediately with `PENDING` status.
   - Background workers handle transcription, analysis, chunking, and embedding generation.
   - Client polls or streams live status (`PENDING` -> `PROCESSING` -> `COMPLETED` / `FAILED`).

4. **Zero-Hallucination Guardrails**:
   - Strict prompt engineering forcing the LLM to rely solely on provided transcript context.
   - Fallback responses (`"Not specified"`, `"I couldn't find that information in this meeting."`) when data is missing.
   - Source attribution containing exact speaker and timestamp ranges `[MM:SS]` linking directly to audio playback.
