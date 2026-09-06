# MeetMind REST API Specification

Welcome to the MeetMind REST API documentation. All API endpoints are versioned under `/api/v1`.

---

## Base URL & Headers

- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json` (except audio upload which uses `multipart/form-data`)
- **Authentication**: `Authorization: Bearer <JWT_ACCESS_TOKEN>`

---

## Authentication Endpoints

### 1. Register User
- **POST** `/auth/register`
- **Description**: Registers a new user account and returns an access token.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Jane Doe"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "email": "user@example.com",
      "full_name": "Jane Doe",
      "is_active": true,
      "created_at": "2026-09-07T00:00:00Z"
    }
  }
  ```

### 2. Login User
- **POST** `/auth/login`
- **Description**: Authenticates user credentials and returns an access token.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "email": "user@example.com",
      "full_name": "Jane Doe",
      "is_active": true,
      "created_at": "2026-09-07T00:00:00Z"
    }
  }
  ```

### 3. Get Current User Profile
- **GET** `/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response** (`200 OK`):
  ```json
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "is_active": true,
    "created_at": "2026-09-07T00:00:00Z"
  }
  ```

---

## Health & System Status

### System Healthcheck
- **GET** `/health`
- **Response** (`200 OK`):
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-09-07T02:00:00Z",
    "database": "connected",
    "redis": "connected"
  }
  ```

---

## Meetings Endpoints

### 1. List Meetings
- **GET** `/meetings`
- **Query Parameters**:
  - `limit` (optional, default `20`): Number of items per page.
  - `offset` (optional, default `0`): Pagination offset.
  - `status` (optional): Filter by status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- **Response** (`200 OK`):
  ```json
  {
    "total": 12,
    "items": [
      {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "title": "Q3 Product Strategy Sync",
        "description": "Discussion on roadmap priorities and feature delivery",
        "status": "COMPLETED",
        "duration_seconds": 1845.5,
        "audio_path": "/app/storage/uploads/q3_sync.mp3",
        "created_at": "2026-09-07T01:15:00Z",
        "updated_at": "2026-09-07T01:20:00Z"
      }
    ]
  }
  ```

### 2. Upload Meeting Audio
- **POST** `/meetings/upload`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Audio file (`.mp3`, `.wav`, `.m4a`, `.mp4`, `.aac`, `.flac`, max 100MB).
  - `title` (optional): Meeting title (defaults to filename).
  - `description` (optional): Short meeting overview.
- **Response** (`201 Created`):
  ```json
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "title": "Q3 Product Strategy Sync",
    "description": "Discussion on roadmap priorities and feature delivery",
    "status": "PENDING",
    "duration_seconds": null,
    "audio_path": "storage/uploads/q3_sync.mp3",
    "created_at": "2026-09-07T01:15:00Z",
    "updated_at": "2026-09-07T01:15:00Z"
  }
  ```

### 3. Global Meeting & Content Search
- **GET** `/meetings/search`
- **Query Parameters**:
  - `q` (required): Search query string.
  - `limit` (optional, default `20`): Maximum results to return.
- **Response** (`200 OK`):
  ```json
  {
    "query": "Kubernetes migration",
    "total": 3,
    "results": [
      {
        "meeting_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "meeting_title": "Infrastructure Architecture Review",
        "match_type": "transcript",
        "snippet": "We agreed to begin the Kubernetes cluster migration next Tuesday.",
        "timestamp": 412.5,
        "score": 0.89
      }
    ]
  }
  ```

### 4. Get Meeting Details
- **GET** `/meetings/{meeting_id}`
- **Response** (`200 OK`): Full meeting object with timestamps, status, duration, and metadata.

### 5. Stream Meeting Audio
- **GET** `/meetings/{meeting_id}/audio`
- **Response**: Binary audio stream (`audio/mpeg`, `audio/wav`, etc.) supporting `Range` headers for seeking.

### 6. Get Processing Status
- **GET** `/meetings/{meeting_id}/status`
- **Response** (`200 OK`):
  ```json
  {
    "meeting_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "status": "PROCESSING",
    "progress_pct": 65,
    "current_stage": "extracting_intelligence",
    "error_message": null
  }
  ```

### 7. Trigger Meeting Reprocessing
- **POST** `/meetings/{meeting_id}/process`
- **Response** (`202 Accepted`):
  ```json
  {
    "message": "Processing pipeline initiated",
    "meeting_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "status": "PROCESSING"
  }
  ```

### 8. Export Meeting Artifacts
- **GET** `/meetings/{meeting_id}/export?format={md|json|txt}`
- **Response**: Formatted file download containing executive summary, key points, action items, decisions, topics, and transcript.

---

## Transcript Endpoints

### 1. Get Complete Transcript
- **GET** `/meetings/{meeting_id}/transcript`
- **Response** (`200 OK`):
  ```json
  {
    "meeting_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "full_text": "Good morning everyone. Today we are discussing the Q3 roadmap...",
    "segment_count": 42,
    "segments": [
      {
        "id": "1a2b3c4d-...",
        "speaker": "Speaker 1",
        "text": "Good morning everyone. Today we are discussing the Q3 roadmap.",
        "start_time": 0.0,
        "end_time": 4.5,
        "confidence": 0.98
      }
    ]
  }
  ```

### 2. Search Meeting Transcript
- **GET** `/meetings/{meeting_id}/transcript/search?q={query}`
- **Response** (`200 OK`): Matched segments with timestamps and highlighted text matches.

---

## Intelligence & Extraction Endpoints

### 1. Executive & Detailed Summary
- **GET** `/meetings/{meeting_id}/summary`
- **Response** (`200 OK`):
  ```json
  {
    "executive_summary": "The team agreed to prioritize backend performance optimizations before launching the self-serve portal.",
    "short_summary": "Q3 roadmap review focusing on database migration, indexing, and UI polish.",
    "detailed_summary": "Full comprehensive multi-paragraph breakdown of meeting sections..."
  }
  ```

### 2. Action Items
- **GET** `/meetings/{meeting_id}/actions`
- **Response** (`200 OK`):
  ```json
  [
    {
      "id": "8f3b2a1c-...",
      "task": "Benchmark pgvector index rebuild latency",
      "assignee": "Sarah Connor",
      "deadline": "2026-09-15",
      "source_timestamp": 312.0,
      "is_completed": false
    }
  ]
  ```

### 3. Toggle Action Item Completion
- **PATCH** `/meetings/{meeting_id}/actions/{action_id}/toggle`
- **Response** (`200 OK`): Updated action item object with inverted `is_completed` boolean.

### 4. Decisions
- **GET** `/meetings/{meeting_id}/decisions`
- **Response** (`200 OK`):
  ```json
  [
    {
      "id": "5e4d3c2b-...",
      "decision": "Adopt Next.js 14 App Router for all internal admin tooling",
      "source_timestamp": 645.0
    }
  ]
  ```

### 5. Topics
- **GET** `/meetings/{meeting_id}/topics`
- **Response** (`200 OK`):
  ```json
  [
    {
      "id": "9a8b7c6d-...",
      "topic": "Database Architecture",
      "summary": "Evaluation of pgvector vs dedicated vector databases for RAG."
    }
  ]
  ```

### 6. Full Intelligence Package
- **GET** `/meetings/{meeting_id}/insights`
- **Response** (`200 OK`): Unified payload containing summaries, action items, decisions, topics, risks, and follow-up questions.

---

## Ask This Meeting (Grounded RAG) Endpoints

### 1. Direct Question / Query
- **POST** `/meetings/{meeting_id}/ask`
- **Request Body**:
  ```json
  {
    "query": "What did Sarah say about the database migration deadline?",
    "session_id": "optional-session-uuid"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "session_id": "91a8b7c6-...",
    "answer": "Sarah confirmed that the database migration must be completed by September 15th to unblock the staging release.",
    "sources": [
      {
        "speaker": "Speaker 2",
        "text": "We need the migration completed by September 15th before staging cut-off.",
        "start_time": 312.0,
        "end_time": 318.5,
        "relevance_score": 0.94
      }
    ]
  }
  ```

### 2. Chat Sessions List
- **GET** `/meetings/{meeting_id}/chat/sessions`
- **Response** (`200 OK`): Array of chat session history objects.

### 3. Chat Session Messages
- **GET** `/meetings/{meeting_id}/chat/sessions/{session_id}/messages`
- **Response** (`200 OK`): Chronological list of user questions and AI grounded answers with citations.

---

## Analytics Endpoints

### 1. Overview Analytics
- **GET** `/analytics/overview`
- **Response** (`200 OK`):
  ```json
  {
    "total_meetings": 24,
    "total_duration_hours": 18.5,
    "total_action_items": 58,
    "completed_action_items": 42,
    "action_item_completion_rate": 72.4,
    "total_decisions": 31,
    "top_topics": [
      {"name": "Architecture", "count": 14},
      {"name": "Frontend", "count": 9},
      {"name": "DevOps", "count": 7}
    ],
    "duration_distribution": {
      "0-15m": 6,
      "15-30m": 10,
      "30-60m": 6,
      "60m+": 2
    }
  }
  ```

---

## Error Handling & Status Codes

All errors return a standardized JSON error response:

```json
{
  "detail": "Error message description",
  "error_code": "RESOURCE_NOT_FOUND",
  "status_code": 404
}
```

| HTTP Status | Meaning | Typical Scenario |
| :--- | :--- | :--- |
| `400 Bad Request` | Invalid input or unprocessable audio format | Non-audio file uploaded |
| `401 Unauthorized` | Missing, expired, or invalid JWT token | Authentication header missing |
| `403 Forbidden` | Accessing a meeting owned by another user | Strict isolation check |
| `404 Not Found` | Target resource does not exist | Meeting or action item ID not found |
| `422 Unprocessable Entity` | Pydantic validation failure | Malformed JSON payload |
| `429 Too Many Requests` | Rate limit exceeded | Exceeded 60 requests/min rate limit |
| `500 Internal Error` | Unhandled server exception | OpenAI API downtime or unhandled error |
