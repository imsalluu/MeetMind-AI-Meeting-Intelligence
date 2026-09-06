# MeetMind RAG (Retrieval-Augmented Generation) Architecture

## Overview
MeetMind implements a hybrid transcript-grounded RAG engine enabling users to "Ask This Meeting" any question with strict factual fidelity and source timestamp jump links.

## Retrieval Pipeline

```
User Query
    │
    ▼
1. Query Preprocessing & Normalization
    │
    ▼
2. Embedding Generation (text-embedding-3-small)
    │
    ├─────────────────────────────┬─────────────────────────────┐
    ▼                             ▼                             ▼
Vector Similarity Search      Full-Text Search              Metadata Filter
(pgvector cosine distance)    (PostgreSQL tsvector / ILIKE) (meeting_id filter)
    │                             │                             │
    └─────────────────────────────┴─────────────────────────────┘
                                  │
                                  ▼
3. Reciprocal Rank Fusion (RRF) & Relevance Scoring
                                  │
                                  ▼
4. Context Formatting (Inject speaker tags and [MM:SS] timestamp headers)
                                  │
                                  ▼
5. Grounded LLM Generation (System Prompt Guardrails)
                                  │
                                  ▼
Response JSON: { "answer": "...", "sources": [ { "timestamp": "...", "text": "..." } ] }
```

## Grounding Rules
1. **Transcript Context Only**: The model is instructed to refuse outside knowledge.
2. **Unsupported Questions**: If query details cannot be answered from retrieved chunks, output `"I couldn't find that information in this meeting."`
3. **Clickable Citations**: Every citation provides exact `start_time` and `end_time` so the frontend audio player and transcript viewer can synchronize to that moment.
