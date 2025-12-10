---
id: api_spec
type: atom
status: draft
depends_on: [features, data_model]
---

# API Specification

> **Note:** MVP is local-only. This spec is for the optional sync feature in v0.3+.

## Base URL

```
https://api.tasktracker.example/v1
```

## Authentication

Bearer token in header:
```
Authorization: Bearer <token>
```

Tokens obtained via magic link (no passwords).

---

## Endpoints

### Create Task

`POST /tasks`

**Request:**
```json
{
  "text": "Fix login bug"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Fix login bug",
  "completed": false,
  "createdAt": "2025-01-15T10:30:00Z"
}
```

---

### List Tasks

`GET /tasks`

**Query params:**
- `q` - Search query (optional)
- `completed` - Filter by status: `true`, `false`, or omit for all

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": "...",
      "text": "Fix login bug",
      "completed": false,
      "createdAt": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

---

### Update Task

`PATCH /tasks/:id`

**Request:**
```json
{
  "completed": true
}
```

**Response (200 OK):**
```json
{
  "id": "...",
  "text": "Fix login bug",
  "completed": true,
  "createdAt": "2025-01-15T10:30:00Z",
  "completedAt": "2025-01-15T14:22:00Z"
}
```

---

### Delete Task

`DELETE /tasks/:id`

**Response (204 No Content)**

---

## Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Task text cannot be empty"
  }
}
```

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `VALIDATION_ERROR` | 400 | Bad input |
| `NOT_FOUND` | 404 | Task doesn't exist |
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `RATE_LIMITED` | 429 | Too many requests |
