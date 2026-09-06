# MeetMind AI Processing Pipeline

## Pipeline Overview
The audio processing pipeline transitions meeting recordings through structured stages:

```
Audio Upload
    │
    ▼
1. Validation (MIME type, size, audio integrity)
    │
    ▼
2. Transcription (OpenAI Whisper with timestamped segments)
    │
    ▼
3. Transcript Normalization (Clean structured segments: speaker, text, start_time, end_time)
    │
    ▼
4. Meeting Intelligence Extraction (Structured LLM generation with Pydantic validation)
   ├── Executive & Detailed Summaries
   ├── Key Discussion Points
   ├── Decisions (with source timestamps)
   ├── Action Items (task, assignee, deadline, source timestamp)
   ├── Topics & Summaries
   └── Risks & Follow-up Questions
    │
    ▼
5. Transcript Chunking & Embedding Generation
   ├── Sliding window segment chunking with metadata
   ├── OpenAI text-embedding-3-small (1536 dims)
   └── pgvector indexing in PostgreSQL
    │
    ▼
Status = COMPLETED
```

## Structured Output & Hallucination Prevention
All extraction calls utilize OpenAI structured output formats validated against Pydantic schemas:
- **No Guessing**: If an assignee or deadline is not explicitly named, the field is assigned `"Not specified"`.
- **Timestamp Traceability**: Decisions and action items capture the exact second `source_timestamp` from the transcript segment where they were agreed upon.
