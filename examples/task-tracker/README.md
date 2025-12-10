# Task Tracker - Ontos Example Project

A minimal example showing Ontos in action. This isn't a real app—it's documentation for a hypothetical task tracker, demonstrating how Ontos structures project knowledge.

## What's Inside

```
docs/
├── kernel/
│   └── mission.md          # Why this project exists
├── strategy/
│   ├── target_audience.md  # Who it's for
│   └── roadmap.md          # Where it's going
├── product/
│   ├── features.md         # What it does
│   └── user_flows.md       # How users interact
└── atom/
    ├── data_model.md       # How data is structured
    └── api_spec.md         # Technical API details
```

## The Dependency Graph

```
mission (kernel)
    └── target_audience (strategy)
            └── roadmap (strategy)
                    └── features (product)
                            ├── user_flows (product)
                            ├── data_model (atom)
                            └── api_spec (atom)
```

## Try It

### 1. Generate the Context Map

```bash
cd examples/task-tracker
python3 ../../.ontos/scripts/ontos_generate_context_map.py --dir docs
```

You should see:
```
Successfully generated Ontos_Context_Map.md
Scanned 7 documents, found 1 issues.
```

> **Note:** The 1 issue is expected—`api_spec.md` is flagged as an "orphan" because nothing depends on it. In a real project, implementation docs would reference the API spec. This is intentional: it shows how Ontos catches disconnected documentation.

### 2. Explore the Map

```bash
cat ../../Ontos_Context_Map.md
```

The context map is generated in the project root. Notice how each document shows its type, status, and dependencies.

### 3. Test with Your AI Tool

Open Claude Code, Cursor, or your preferred AI tool and try:

> "Activate Ontos. I want to add a 'due date' feature to tasks."

Watch how it:
1. Reads `Ontos_Context_Map.md`
2. Loads `features.md` (where features are defined)
3. Follows dependencies to `target_audience.md` (to understand who it's for)
4. Confirms what context it loaded

### 4. Try a Migration Scenario

Imagine rewriting this from React to Svelte. Ask your AI:

> "Activate Ontos. We're rewriting the frontend from React to Svelte. What decisions need to carry over?"

The AI should identify that:
- `kernel/`, `strategy/`, `product/` docs are unchanged (decisions survive)
- `atom/` docs need rewriting (implementation details change)

## What to Notice

| Observation | Why It Matters |
|-------------|----------------|
| Atoms depend on Products, not vice versa | Technical specs reference features, keeping product decisions stable |
| Strategy connects to Mission | Every goal traces back to "why we exist" |
| No circular dependencies | The graph is clean and navigable |
| `api_spec.md` is marked `draft` | Status field shows what's settled vs speculative |
| `api_spec.md` flagged as orphan | Ontos detects disconnected docs—useful for finding dead documentation |

## Exercises

1. **Add a new feature**: Create `docs/product/keyboard_shortcuts.md` with proper frontmatter. What should it depend on?

2. **Break the rules**: Make `mission.md` depend on `api_spec.md`. Run the validator and see what happens.

3. **Trace a decision**: If you changed the mission from "solo developers" to "small teams," which documents would need updating?
