---
id: features
type: product
status: active
depends_on: [roadmap]
---

# Features

## MVP Feature Set

### Quick Add
- Single text input, always visible
- Press Enter to create task
- Input clears and stays focused
- No modal, no form, no friction

### List View
- All tasks visible (no pagination for MVP)
- Sorted by creation date (newest first)
- Completed tasks show strikethrough
- Completed tasks sink to bottom

### Mark Complete
- Click checkbox to toggle
- Keyboard: select task + press `x`
- Reversible (uncheck to restore)

### Search
- Press `/` to focus search input
- Fuzzy matching on task text
- Real-time filtering as you type
- Escape to clear and show all

## Future Features (v0.2+)

- **Tags**: Prefix with `#` to auto-tag (e.g., "Fix bug #backend")
- **Due dates**: Optional, shows countdown when set
- **Keyboard navigation**: `j`/`k` to move, `x` to complete, `e` to edit

## Anti-Features (Never Building)

- Subtasks (use separate tasks instead)
- Priority levels (if everything is priority, nothing is)
- Recurring tasks (too complex for MVP audience)
- Time tracking
