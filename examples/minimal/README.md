# Minimal Ontos Example

This folder shows a working Ontos setup with 3 files.

## Files

```
docs/
├── kernel/mission.md      # Why (foundational)
├── strategy/audience.md   # Who (business)
└── atom/data_model.md     # How (technical)
```

## The Graph

```
mission (kernel)
   └── audience (strategy)
          └── data_model (atom)
```

## Try It

```bash
ontos map
```

## Files Content

### docs/kernel/mission.md
```yaml
---
id: mission
type: kernel
status: active
depends_on: []
---
# Mission
Build the simplest task tracker for solo developers.
```

### docs/strategy/audience.md
```yaml
---
id: audience  
type: strategy
status: active
depends_on: [mission]
---
# Target Audience
Solo developers juggling side projects. Not teams.
```

### docs/atom/data_model.md
```yaml
---
id: data_model
type: atom
status: active
depends_on: [audience]
---
# Data Model
```typescript
interface Task {
  id: string;
  text: string;
  completed: boolean;
}
```
Storage: localStorage (MVP).
```
