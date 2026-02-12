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
