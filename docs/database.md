# MeetMind Database Schema Design

## Overview
MeetMind utilizes PostgreSQL 16 with the `pgvector` extension for storing relational meeting metadata, structured intelligence, and 1536-dimensional embeddings.

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
        timestamp updated_at
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
        timestamp updated_at
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

    CHAT_SESSIONS {
        uuid id PK
        uuid meeting_id FK
        uuid user_id FK
        string title
        timestamp created_at
    }

    CHAT_MESSAGES {
        uuid id PK
        uuid session_id FK
        string role
        text content
        jsonb sources
        timestamp created_at
    }
```
