---
id: user_flows
type: product
status: active
depends_on: [features]
---

# User Flows

## Flow 1: Add a Task

**Trigger:** User has a thought they need to capture.

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User loads app | Input is auto-focused |
| 2 | Types "Fix login bug" | Text appears in input |
| 3 | Presses Enter | Task appears at top of list |
| 4 | — | Input clears, stays focused |

**Time target:** < 2 seconds from thought to captured.

**Edge cases:**
- Empty input + Enter → Nothing happens (no empty tasks)
- Very long text → Truncate display, full text in tooltip

---

## Flow 2: Complete a Task

**Trigger:** User finished a task.

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User clicks checkbox | Checkbox fills |
| 2 | — | Task text gets strikethrough |
| 3 | — | Task animates to bottom of list |

**Keyboard alternative:** Navigate to task with `j`/`k`, press `x`.

---

## Flow 3: Find a Task

**Trigger:** User remembers a task exists but can't see it.

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Presses `/` | Search input focuses |
| 2 | Types "bug" | List filters to matching tasks |
| 3 | Sees "Fix login bug" | Matching text highlighted |
| 4 | Presses Escape | Filter clears, all tasks shown |

**Performance target:** Filter should feel instant (<50ms).

---

## Flow 4: Undo a Completion (Mistake)

**Trigger:** User accidentally marked a task complete.

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User scrolls to completed tasks | Completed section visible |
| 2 | Clicks filled checkbox | Checkbox empties |
| 3 | — | Task moves back to active list |

No confirmation needed. Fully reversible.
