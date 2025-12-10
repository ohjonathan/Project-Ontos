---
id: data_model
type: atom
status: active
depends_on: [features]
---

# Data Model

## Core Entity: Task

```typescript
interface Task {
  id: string;           // UUID v4
  text: string;         // Task content, 1-500 characters
  completed: boolean;   // Default: false
  createdAt: string;    // ISO 8601 timestamp
  completedAt?: string; // ISO 8601, only set when completed
}
```

## Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Fix login bug",
  "completed": false,
  "createdAt": "2025-01-15T10:30:00Z"
}
```

## Storage Strategy

### MVP: localStorage

```typescript
const STORAGE_KEY = 'tasktracker_tasks';

function saveTasks(tasks: Task[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function loadTasks(): Task[] {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : [];
}
```

**Limitations:**
- ~5MB storage limit
- No sync across devices
- Lost if user clears browser data

### Future: IndexedDB

For v0.3+ when we need:
- Larger datasets (1000+ tasks)
- Better query performance
- Offline-first with sync

## Indexes

| Index | Purpose |
|-------|---------|
| Primary key: `id` | Direct lookup |
| Sort: `createdAt DESC` | Default list order |
| Sort: `completedAt DESC` | Completed tasks order |
| Full-text: `text` | Search functionality |
