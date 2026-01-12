# Project Ontos v3.0: Comprehensive Strategic Analysis

**Prepared for:** Johnny (Project Lead)  
**Prepared by:** Technical Co-Founder Analysis  
**Date:** January 8, 2026  
**Document Version:** 1.0  
**Classification:** Internal Strategic Planning

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Philosophy and Tension Analysis](#2-philosophy-and-tension-analysis)
3. [Model Context Protocol (MCP) Deep Dive](#3-model-context-protocol-mcp-deep-dive)
4. [Competitive Landscape Analysis](#4-competitive-landscape-analysis)
5. [Python Packaging Strategy](#5-python-packaging-strategy)
6. [Feature Prioritization Framework](#6-feature-prioritization-framework)
7. [Risk Analysis and Mitigation](#7-risk-analysis-and-mitigation)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Technical Specifications](#9-technical-specifications)
10. [Code Examples and Reference Implementations](#10-code-examples-and-reference-implementations)
11. [Decision Framework](#11-decision-framework)
12. [Appendices](#12-appendices)

---

## 1. Executive Summary

### 1.1 Current State Assessment

Project Ontos v2.9.5 is a mature, well-architected documentation system with:
- ~11,500 lines of Python across 25+ scripts
- 132 tests with comprehensive coverage
- Dual ontology model (Space/Time) that's conceptually sound
- Clean architecture with transactional file operations
- Zero external dependencies (Python stdlib only)
- Tiered curation levels (L0/L1/L2) that lower adoption friction

The system works. The question is: what should v3.0 be?

### 1.2 The Core Question

You've articulated two goals:
1. **MCP-style distribution** where users "plug in and use" without per-directory installation
2. **Simplicity, lightweight, zero friction**

These goals are in tension. This document provides the analysis needed to resolve that tension and chart a clear path forward.

### 1.3 Key Recommendations (Preview)

| Recommendation | Confidence | Rationale |
|----------------|------------|-----------|
| pip install ontos (core CLI) | High | Right distribution model, low risk |
| MCP server as optional package | High | Preserves lightweight core, enables power users |
| Export to CLAUDE.md/AGENTS.md | High | Immediate value, no server needed |
| System daemon as default | Low | Adds operational complexity users don't want |
| S3 backend | Low | Violates local-first, premature optimization |

### 1.4 Strategic Position

Ontos occupies a unique position in the AI coding tool ecosystem:
- **Not competing with:** CLAUDE.md, .cursorrules, AGENTS.md (these are instruction files)
- **Complementing:** All of the above (Ontos provides the semantic layer they reference)
- **Unique value:** Structured knowledge graph with dependency tracking, decision history, staleness detection

This positioning should drive all v3.0 decisions.

---

## 2. Philosophy and Tension Analysis

### 2.1 The Fundamental Tension

Your stated values:

| Value | Implication |
|-------|-------------|
| "Simplicity and lightweight" | Minimal dependencies, small footprint |
| "Zero friction" | Just works, no configuration needed |
| "Curation over ceremony" | Requires intent and human judgment |
| "Local-first, git-native" | Data lives in repo, versioned |

The tension: **"Zero friction" and "Curation over ceremony" are inherently contradictory.**

Curation requires friction. The act of deciding "this matters" IS the friction that creates signal. You cannot have both zero friction and meaningful curation.

### 2.2 Resolution: Friction Gradient

The solution is not to eliminate friction but to create a **friction gradient**:

```
L0 Scaffold  →  L1 Stub  →  L2 Full
(near-zero)     (low)       (intentional)
```

You've already built this with curation levels. The v3.0 question is: how does distribution model affect this gradient?

### 2.3 Daemon Architecture Analysis

Your v3.0 vision includes an MCP server daemon (`ontos serve`). Let's examine what this adds:

**Operational Complexity Added:**
- Process management (start/stop/restart)
- Port binding and potential conflicts
- Authentication token management
- Stale lock detection for concurrent access
- Startup time before first query
- Background process monitoring

**Value Provided:**
- Dynamic queries without regenerating full map
- Real-time staleness detection
- Interactive tool exposure to agents

**The Question:** Is the value worth the complexity?

**My Assessment:** For most users, no. The context map is already readable by any agent. Dynamic queries are a power-user feature. Making the daemon the default experience would be a mistake.

### 2.4 What "Lightweight" Actually Means

Let's define "lightweight" operationally:

| Metric | v2.9.5 (Current) | v3.0 with Daemon | v3.0 without Daemon |
|--------|------------------|------------------|---------------------|
| External dependencies | 0 | 3+ (mcp, fastmcp, etc.) | 0 (core) / 3+ (optional) |
| Memory footprint | ~10MB during operation | ~50MB resident daemon | ~10MB during operation |
| Startup time | <100ms | 1-2s for server init | <100ms |
| Background processes | 0 | 1 (always running) | 0 |
| Port requirements | None | 1 TCP port | None |

The split-package approach (core + optional MCP) preserves lightweight for users who want it while enabling MCP for those who need it.

### 2.5 The "Install Once, Use Everywhere" Promise

You want users to install once and use across projects. Let's examine what this requires:

**Option A: System-wide CLI (pip install)**
```bash
pip install ontos
cd /any/project
ontos init
ontos map
```

This works without a daemon. The CLI is system-wide; the data is per-project. This is exactly how git works.

**Option B: System-wide daemon**
```bash
pip install ontos
ontos serve --background
# Now any project can query the daemon
```

This adds complexity and raises questions:
- Does the daemon serve all projects simultaneously?
- How does it know which project context to use?
- What about project switching?

**Recommendation:** Option A is sufficient for "install once, use everywhere." The daemon doesn't add value for this use case.

### 2.6 When Daemon Makes Sense

A daemon-based architecture is valuable when:
1. **Real-time updates are needed** (file watchers, live queries)
2. **Long-running computations benefit from caching**
3. **Multiple clients need concurrent access to shared state**

For Ontos:
- Real-time updates: Marginal value (context doesn't change that fast)
- Caching: The context map IS the cache
- Concurrent access: Git already handles this

The daemon is a solution looking for a problem. It should be optional, not default.

---

## 3. Model Context Protocol (MCP) Deep Dive

### 3.1 What MCP Actually Is

MCP is a JSON-RPC 2.0 based protocol for connecting AI applications to external data and tools. Key concepts:

**Primitives:**
- **Resources** - Data the LLM can read (like GET endpoints)
- **Tools** - Functions the LLM can call (like POST endpoints)
- **Prompts** - Reusable templates for LLM interactions

**Architecture:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Host      │────▶│   Client    │────▶│   Server    │
│ (Claude,    │     │ (in Host)   │     │ (Ontos)     │
│  Cursor)    │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Transports:**
- stdio (for local CLI tools)
- HTTP/SSE (for networked servers)
- WebSocket (for bidirectional communication)

### 3.2 MCP Specification Timeline

| Date | Version | Key Features |
|------|---------|--------------|
| Nov 2024 | Initial | Core protocol, resources, tools, prompts |
| Jun 2025 | 2025-06-18 | OAuth Resource Servers, structured outputs |
| Nov 2025 | 2025-11-25 | Server-side agent loops, parallel tool calls, Tasks (experimental) |

The protocol is stable and widely adopted. OpenAI, Google, and Anthropic all support it.

### 3.3 Python MCP SDK Analysis

**Official SDK:** `pip install mcp`
- Maintained by Anthropic
- Implements full specification
- Includes FastMCP for high-level server creation
- Current version: 1.25.0

**FastMCP (standalone):** `pip install fastmcp`
- Production-ready framework
- Advanced patterns (composition, proxying, OpenAPI generation)
- Enterprise auth (Google, GitHub, Azure, Auth0)
- FastMCP 1.0 was incorporated into official SDK
- FastMCP 2.0 is the actively maintained version

**Recommendation:** Use official SDK (`mcp`) for Ontos. It's simpler and sufficient for our needs. FastMCP 2.0 is overkill unless we need enterprise auth.

### 3.4 MCP Server Lifecycle

```python
# Initialization
client sends: { "method": "initialize", "params": { "capabilities": {...} } }
server responds: { "result": { "capabilities": {...}, "serverInfo": {...} } }
client sends: { "method": "notifications/initialized" }

# Normal operation
client sends: { "method": "tools/list" }
server responds: { "result": { "tools": [...] } }

client sends: { "method": "tools/call", "params": { "name": "query_deps", "arguments": {...} } }
server responds: { "result": { "content": [...] } }

# Shutdown
client sends: { "method": "shutdown" }
server responds: { "result": null }
```

### 3.5 What Ontos Would Expose via MCP

**Resources (read-only data):**

| Resource URI | Description |
|--------------|-------------|
| `ontos://context-map` | Full context map markdown |
| `ontos://document/{id}` | Single document by ID |
| `ontos://hierarchy/{type}` | All documents of a type |
| `ontos://decision-history` | Decision history ledger |

**Tools (callable functions):**

| Tool Name | Parameters | Returns |
|-----------|------------|---------|
| `query_dependencies` | `doc_id: string` | Dependencies and dependents |
| `check_staleness` | none | List of stale documents |
| `find_by_concept` | `concept: string` | Documents with that concept |
| `get_recent_logs` | `count: int` | Recent session logs |
| `validate_graph` | none | Validation errors |

**Prompts (templates):**

| Prompt Name | Description |
|-------------|-------------|
| `ontos-activate` | Standard activation prompt |
| `ontos-archive` | Session archival prompt |
| `ontos-maintain` | Maintenance check prompt |

### 3.6 MCP Security Considerations

The November 2025 spec includes security requirements:

**Local Server Security:**
- Bind to 127.0.0.1 only (you have this in your v2.9.4 requirements)
- Auto-generated auth token required
- File locking for concurrent access
- No HTTP fallback

**For Ontos:**
```python
# Minimal security implementation
mcp = FastMCP(
    "Ontos",
    host="127.0.0.1",  # Local only
    port=0,  # Auto-assign available port
)

# Token stored in ~/.ontos/auth_token
# Passed via header or query param
```

### 3.7 MCP Adoption Landscape

| Tool | MCP Support | Notes |
|------|-------------|-------|
| Claude Desktop | Native | First-party support |
| Claude Code | Native | Via CLAUDE.md and tools |
| Cursor | Via extensions | MCP client support |
| Windsurf | Via extensions | MCP client support |
| ChatGPT | Native | Since March 2025 |
| GitHub Copilot | Limited | Reads AGENTS.md |

**Key Insight:** MCP is the winning standard. Supporting it is strategic. But you don't need to make it the default experience.

### 3.8 The "Ontos as MCP Resource" Insight

Here's the thing: `Ontos_Context_Map.md` is already a perfectly good MCP resource.

```python
@mcp.resource("ontos://context-map")
def get_context_map() -> str:
    """Returns the full Ontos context map."""
    map_path = get_context_map_path()
    return map_path.read_text()
```

That's it. Your existing system already generates the artifact. MCP just exposes it. The question isn't whether to support MCP—it's whether MCP should be the primary interface or an optional enhancement.

---

## 4. Competitive Landscape Analysis

### 4.1 Context File Ecosystem

The AI coding tool ecosystem has converged on project-level context files:

| File | Tool | Purpose | Format |
|------|------|---------|--------|
| CLAUDE.md | Claude Code | Project instructions | Markdown with sections |
| .cursorrules | Cursor | Project rules | MDX with metadata |
| .copilot-instructions.md | GitHub Copilot | Coding instructions | Markdown |
| AGENTS.md | Cross-tool | Agent instructions | Markdown (emerging standard) |
| .windsurfrules | Windsurf | Project configuration | Similar to Cursor |

**Critical Observation:** These are all **instruction files**. They tell the AI *how to code in this repo*. None of them address *what the project is, why decisions were made, or what depends on what*.

### 4.2 Ontos vs. Instruction Files

| Aspect | CLAUDE.md / .cursorrules | Ontos |
|--------|--------------------------|-------|
| Purpose | How to code | What the project is |
| Content | Instructions, conventions | Knowledge graph, history |
| Structure | Flat sections | Hierarchical with dependencies |
| History | None | Decision history, session logs |
| Validation | None | Broken links, cycles, staleness |
| Dependencies | Not tracked | Explicit `depends_on` |

**This is Ontos's wedge.** You're not competing with instruction files—you're the semantic layer that gives them something to reference.

### 4.3 Realistic User Setup

```
/my-project
├── CLAUDE.md              # "Use TypeScript, prefer functional style..."
├── .cursorrules           # "Follow ESLint config, use Prettier..."
├── AGENTS.md              # "Run tests before committing..."
├── Ontos_Context_Map.md   # "Here's what this project IS"
└── docs/
    ├── kernel/
    │   └── mission.md     # Why we exist
    ├── strategy/
    │   └── v2_roadmap.md  # Where we're going
    └── atom/
        └── auth_flow.md   # How auth works
```

The agent reads CLAUDE.md for *instructions* and Ontos for *context*. Orthogonal concerns.

### 4.4 Knowledge Management Tools

| Tool | Approach | Ontos Differentiator |
|------|----------|---------------------|
| Notion | Cloud database, rich UI | Local-first, git-native |
| Obsidian | Local markdown, backlinks | Explicit types, validation |
| Confluence | Enterprise wiki | Developer-focused, AI-optimized |
| GitBook | Documentation hosting | Embedded in repo |
| RAG/Vector DB | Semantic search | Structure over search |

**Key Differentiator:** Ontos is **explicit and deterministic**. No semantic search, no probability. When you ask "what does auth depend on?", you get the declared dependencies, not a probabilistic guess.

### 4.5 AI Context Management Tools

| Tool | What It Does | Ontos Comparison |
|------|--------------|------------------|
| Context7 | Up-to-date docs for LLMs | Ontos is project-specific, not generic docs |
| mem.ai | Personal memory for AI | Ontos is project memory, not personal |
| Augment | Multi-repo context | Ontos is single-repo (for now) |
| Qodo | PR-aware suggestions | Ontos is doc-aware, not PR-aware |

**Gap Identified:** No tool provides **structured project knowledge with decision history** that works across AI tools. This is Ontos's unique value.

### 4.6 Symlink Strategy (Emerging Pattern)

From my research, teams are starting to use symlinks to maintain one context file:

```bash
# Maintain one source of truth
ln -s PROJECT_CONTEXT.md CLAUDE.md
ln -s PROJECT_CONTEXT.md .cursorrules
ln -s PROJECT_CONTEXT.md AGENTS.md
```

**Opportunity for Ontos:** Generate these files from the context map:

```bash
ontos export --format claude.md
ontos export --format cursor-rules
ontos export --format agents.md
```

This makes Ontos the *source of truth* that generates tool-specific artifacts.

### 4.7 Market Positioning Summary

```
                    ┌─────────────────────────────────────┐
                    │     AI Coding Tool Ecosystem        │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼───────┐          ┌───────▼───────┐          ┌───────▼───────┐
│  Instructions │          │    Context    │          │   Execution   │
│ (How to code) │          │ (What it is)  │          │  (Do tasks)   │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
   CLAUDE.md                    ONTOS                      Claude Code
   .cursorrules                (unique)                     Cursor Agent
   AGENTS.md                                                  Codex
```

Ontos occupies the "Context" layer—a space currently empty.

---

## 5. Python Packaging Strategy

### 5.1 Current Distribution Model

```
User downloads → Runs install.py → Copies .ontos/ to project
```

Problems:
- Requires curl or manual download
- Per-project installation
- Updates require re-running installer
- Not discoverable via PyPI

### 5.2 Target Distribution Model

```bash
pip install ontos
cd /any/project
ontos init
```

Benefits:
- Standard Python distribution
- System-wide installation
- Updates via pip upgrade
- Discoverable on PyPI
- Works with virtual environments

### 5.3 Package Structure Options

**Option A: Single Package (Simple)**
```
ontos/
├── __init__.py
├── cli.py           # Entry point
├── core/
│   ├── context.py
│   ├── schema.py
│   └── ...
├── commands/
│   ├── init.py
│   ├── map.py
│   ├── log.py
│   └── ...
└── templates/
    └── ...
```

```toml
# pyproject.toml
[project]
name = "ontos"
dependencies = []  # Zero deps!

[project.scripts]
ontos = "ontos.cli:main"
```

**Option B: Split Packages (Recommended)**
```
ontos/              # Core package, zero deps
ontos-mcp/          # MCP server, has deps
```

```toml
# ontos/pyproject.toml
[project]
name = "ontos"
dependencies = []

# ontos-mcp/pyproject.toml
[project]
name = "ontos-mcp"
dependencies = [
    "ontos",
    "mcp>=1.0.0",
]
```

**Option C: Single Package with Optional Deps**
```toml
[project]
name = "ontos"
dependencies = []

[project.optional-dependencies]
mcp = ["mcp>=1.0.0"]
```

```bash
pip install ontos        # Core only
pip install ontos[mcp]   # With MCP support
```

**Recommendation:** Option C is the cleanest. Single package, optional MCP. Users who don't need MCP never see the complexity.

### 5.4 Entry Points Configuration

```toml
[project.scripts]
ontos = "ontos.cli:main"

[project.entry-points."ontos.commands"]
init = "ontos.commands.init:InitCommand"
map = "ontos.commands.map:MapCommand"
log = "ontos.commands.log:LogCommand"
# ... etc
```

This enables plugin architecture for future extensions.

### 5.5 Template and Asset Handling

Current approach uses file copies. For pip packages, use `importlib.resources`:

```python
# ontos/templates/__init__.py
from importlib.resources import files

def get_template(name: str) -> str:
    return files("ontos.templates").joinpath(name).read_text()
```

```python
# Usage
from ontos.templates import get_template
mission_template = get_template("mission.md.template")
```

### 5.6 Configuration Migration

Current: `ontos_config.py` generated in project
Target: Keep same approach, it works

```python
# ontos/config.py
def get_config():
    # 1. Check for project-level config
    project_config = Path.cwd() / ".ontos" / "config.py"
    if project_config.exists():
        return load_config(project_config)
    
    # 2. Fall back to defaults
    return DEFAULT_CONFIG
```

### 5.7 Version Management

```toml
[project]
name = "ontos"
version = "3.0.0"
```

```python
# ontos/__init__.py
__version__ = "3.0.0"
```

Use `setuptools_scm` or manual version bumping. Given your frequent releases, manual is probably fine.

### 5.8 Publishing Workflow

```bash
# Build
python -m build

# Test on TestPyPI
python -m twine upload --repository testpypi dist/*

# Publish to PyPI
python -m twine upload dist/*
```

GitHub Actions workflow:
```yaml
name: Publish to PyPI
on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

### 5.9 Backward Compatibility

Users with v2.x installations need a migration path:

```bash
# Detect old installation
if [ -d ".ontos/scripts" ]; then
    echo "Detected v2.x installation"
    echo "Run 'ontos migrate-from-v2' to upgrade"
fi
```

```python
# ontos/commands/migrate_from_v2.py
def migrate():
    # 1. Backup existing .ontos/
    # 2. Remove scripts/ (now in pip package)
    # 3. Keep config, templates, hooks
    # 4. Update hook scripts to use new CLI
```

---

## 6. Feature Prioritization Framework

### 6.1 Prioritization Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| User Value | 40% | Does it solve a real problem users have? |
| Strategic Fit | 25% | Does it align with Ontos's unique position? |
| Implementation Risk | 20% | How likely to cause problems? |
| Maintenance Burden | 15% | Ongoing cost to support? |

### 6.2 Feature Analysis

#### 6.2.1 pip install ontos

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 9/10 | Eliminates friction of manual install |
| Strategic Fit | 10/10 | Standard distribution, discoverable |
| Implementation Risk | 2/10 | Well-understood problem |
| Maintenance Burden | 2/10 | PyPI handles distribution |
| **Weighted Score** | **8.8** | **Must Have** |

#### 6.2.2 MCP Server (Optional Package)

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 6/10 | Power users only, most don't need |
| Strategic Fit | 8/10 | Aligns with ecosystem direction |
| Implementation Risk | 5/10 | New dependency, protocol complexity |
| Maintenance Burden | 6/10 | Protocol may evolve |
| **Weighted Score** | **6.4** | **Should Have** |

#### 6.2.3 Export to CLAUDE.md/AGENTS.md

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 9/10 | Immediate value, no learning curve |
| Strategic Fit | 10/10 | Positions Ontos as source of truth |
| Implementation Risk | 2/10 | Template generation is simple |
| Maintenance Burden | 4/10 | Need to track format changes |
| **Weighted Score** | **8.5** | **Must Have** |

#### 6.2.4 Typed Edges

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 7/10 | More expressive relationships |
| Strategic Fit | 9/10 | Richer knowledge graph |
| Implementation Risk | 4/10 | Schema change, migration needed |
| Maintenance Burden | 3/10 | Once implemented, stable |
| **Weighted Score** | **7.0** | **Should Have** |

#### 6.2.5 VS Code Extension

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 5/10 | Nice to have, not essential |
| Strategic Fit | 6/10 | Increases visibility |
| Implementation Risk | 6/10 | New codebase, different ecosystem |
| Maintenance Burden | 7/10 | VS Code updates, user support |
| **Weighted Score** | **5.5** | **Could Have (v3.5+)** |

#### 6.2.6 Cross-Repo Federation

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 6/10 | Enterprise need, not individual |
| Strategic Fit | 7/10 | Extends value proposition |
| Implementation Risk | 8/10 | Complex distributed system problem |
| Maintenance Burden | 8/10 | Sync conflicts, versioning issues |
| **Weighted Score** | **6.0** | **Could Have (v4.0+)** |

#### 6.2.7 S3 Backend

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 3/10 | Very niche use case |
| Strategic Fit | 3/10 | Violates local-first principle |
| Implementation Risk | 5/10 | AWS dependency, auth complexity |
| Maintenance Burden | 6/10 | Cloud provider changes |
| **Weighted Score** | **3.4** | **Should NOT Have** |

#### 6.2.8 AI-Assisted Tagging

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| User Value | 6/10 | Convenience, but undermines curation |
| Strategic Fit | 4/10 | Conflicts with "curation over ceremony" |
| Implementation Risk | 7/10 | LLM dependency, quality variance |
| Maintenance Burden | 7/10 | Model updates, prompt engineering |
| **Weighted Score** | **5.2** | **Should NOT Have** |

### 6.3 Prioritized Feature List

| Priority | Feature | Version | Rationale |
|----------|---------|---------|-----------|
| 1 | pip install ontos | v3.0.0 | Foundation for everything else |
| 2 | Export to CLAUDE.md/AGENTS.md | v3.1.0 | Immediate value, low risk |
| 3 | Typed edges | v3.1.0 | Schema enhancement |
| 4 | MCP Server (optional) | v3.2.0 | Power user feature |
| 5 | Context file detection | v3.2.0 | Better integration |
| 6 | VS Code status extension | v3.5.0 | Nice to have |
| 7 | Cross-repo federation | v4.0.0 | Major architectural change |

### 6.4 The 80/20 Feature

**Question:** What single feature would unlock the most adoption with the least effort?

**Answer:** `ontos export --format agents.md`

**Rationale:**
- AGENTS.md is emerging as the cross-tool standard
- Generating it from Ontos makes Ontos the source of truth
- No server needed, just a template transformation
- Works with Claude Code, Cursor, Copilot, Windsurf
- Users get value immediately without learning new tools

**Implementation Effort:** ~2 days

**Expected Impact:** High. Users can adopt Ontos without changing their existing workflow. They maintain Ontos docs, and their existing tools automatically benefit.

---

## 7. Risk Analysis and Mitigation

### 7.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MCP adoption slows | Low | Medium | Keep MCP optional, core works without |
| Context windows grow huge | High | Medium | Pivot value prop to structure over tokens |
| pip package conflicts | Medium | High | Pin deps carefully, test matrix |
| v3.0 breaks v2.x | Medium | High | Schema migration, deprecation warnings |
| Users don't curate | High | High | Better scaffolding, L0 defaults |
| Competition emerges | Medium | Medium | Move fast, maintain differentiation |

### 7.2 Detailed Risk Analysis

#### 7.2.1 Risk: MCP Adoption Slows

**Scenario:** MCP loses momentum, tools stop supporting it.

**Likelihood:** Low (20%)
- MCP is now under Linux Foundation (Agentic AI Foundation)
- OpenAI, Google, Anthropic all support it
- Network effects are strong

**Impact:** Medium
- Ontos's core value doesn't depend on MCP
- Context map is readable without MCP

**Mitigation:**
- Keep MCP as optional package
- Core functionality works via CLI
- Export formats provide alternative integration path

#### 7.2.2 Risk: Context Windows Grow to 1M+ Tokens

**Scenario:** AI context windows become so large that structured context matters less.

**Likelihood:** High (80%)
- Google Gemini already offers 1M tokens
- Trend is clearly toward larger windows

**Impact:** Medium
- Token savings becomes less valuable
- BUT structure and navigation remain valuable

**Mitigation:**
- Pivot messaging from "token efficiency" to "navigable structure"
- Emphasize decision history (can't be generated, only captured)
- Emphasize validation (broken links, staleness)
- "Big context window doesn't mean infinite; structure still helps"

#### 7.2.3 Risk: pip Package Dependency Conflicts

**Scenario:** Ontos's dependencies conflict with user's project.

**Likelihood:** Medium (40%)
- Common with Python packages
- Especially risky with MCP SDK

**Impact:** High
- Users can't install
- Bad first impression

**Mitigation:**
- Core package has ZERO dependencies
- MCP is optional (`pip install ontos[mcp]`)
- Test against common environments
- Document compatibility matrix

#### 7.2.4 Risk: v3.0 Breaks v2.x Workflows

**Scenario:** Existing users have scripts or workflows that break.

**Likelihood:** Medium (50%)
- Schema changes
- CLI differences
- Hook changes

**Impact:** High
- Losing existing users is costly
- Reputation damage

**Mitigation:**
- Schema versioning already in place (2.0-2.2, planning 3.0)
- Migration tooling (`ontos migrate --check`, `--apply`)
- Deprecation warnings (already doing in v2.9.2)
- Maintain backward-compatible aliases
- Clear upgrade guide

#### 7.2.5 Risk: Users Don't Want to Curate

**Scenario:** Friction of curation prevents adoption.

**Likelihood:** High (70%)
- This is the fundamental tension
- Most users want magic, not work

**Impact:** High
- Core value prop depends on curation
- Without curation, Ontos is just another file dump

**Mitigation:**
- L0 scaffolding (already implemented)
- Better defaults (auto-generate from git history?)
- Clear onboarding path
- Emphasize value of curation (decision history)
- Case studies showing ROI of curation

#### 7.2.6 Risk: Competition Emerges

**Scenario:** A well-funded competitor builds similar tool.

**Likelihood:** Medium (40%)
- Space is heating up
- Big companies (GitHub, JetBrains) could build this

**Impact:** Medium
- First-mover advantage matters less than execution
- Open source provides moat

**Mitigation:**
- Move fast on v3.0
- Build community (contributors, users)
- Stay focused on unique value (curated structure)
- Avoid feature bloat

### 7.3 Risk-Adjusted Roadmap

Given the risks, here's an adjusted roadmap:

| Phase | Focus | Risk Mitigation |
|-------|-------|-----------------|
| v3.0.0 | pip packaging | Zero deps, clean migration |
| v3.0.1 | Bug fixes | Quick iteration on issues |
| v3.1.0 | Export formats | Immediate value, low risk |
| v3.2.0 | MCP (optional) | Don't break core users |
| v3.x | Respond to market | Stay agile |

---

## 8. Implementation Roadmap

### 8.1 Phase 1: Packaging Foundation (v3.0.0)

**Duration:** 2-3 weeks

**Deliverables:**
1. Package structure (ontos/)
2. pyproject.toml configuration
3. CLI entry points
4. Template handling via importlib.resources
5. Migration script from v2.x
6. GitHub Actions for PyPI publishing
7. Documentation updates

**Success Criteria:**
- `pip install ontos` works
- All existing CLI commands work
- v2.x users can migrate without data loss
- Tests pass on Python 3.9, 3.10, 3.11, 3.12

**Architecture:**
```
ontos/
├── __init__.py          # Version, exports
├── __main__.py          # python -m ontos
├── cli.py               # Click-based CLI
├── core/                # Existing core modules
│   ├── context.py
│   ├── schema.py
│   ├── curation.py
│   ├── staleness.py
│   ├── history.py
│   ├── paths.py
│   ├── frontmatter.py
│   └── config.py
├── commands/            # CLI command implementations
│   ├── init.py
│   ├── map.py
│   ├── log.py
│   ├── verify.py
│   ├── maintain.py
│   ├── consolidate.py
│   ├── query.py
│   ├── scaffold.py
│   ├── stub.py
│   ├── promote.py
│   ├── migrate.py
│   └── update.py
├── templates/           # Starter templates
│   ├── mission.md.template
│   ├── roadmap.md.template
│   └── decision_history.md.template
├── hooks/               # Git hook scripts
│   ├── pre-push
│   └── pre-commit
└── ui/
    └── output.py        # OutputHandler
```

### 8.2 Phase 2: Export Formats (v3.1.0)

**Duration:** 1-2 weeks

**Deliverables:**
1. `ontos export --format <format>` command
2. Format templates for:
   - `claude.md` (CLAUDE.md format)
   - `cursor-rules` (.cursorrules format)
   - `agents.md` (AGENTS.md format)
   - `copilot` (.copilot-instructions.md format)
3. Auto-sync option (regenerate on map change)
4. Format detection (read existing files)

**Success Criteria:**
- Export generates valid format for each tool
- Exported files work with target tools
- Round-trip: export → tool uses → no issues

**Command Interface:**
```bash
# Export to specific format
ontos export --format agents.md

# Export to multiple formats
ontos export --format agents.md --format claude.md

# Auto-sync (regenerate when map changes)
ontos export --format agents.md --auto-sync

# Show what would be generated
ontos export --format agents.md --dry-run
```

### 8.3 Phase 3: Typed Edges (v3.1.0)

**Duration:** 1 week

**Deliverables:**
1. Schema update for typed edges
2. New edge types: `implements`, `tests`, `deprecates`, `references`
3. Migration for existing `depends_on` (becomes generic dependency)
4. Query enhancements for edge types
5. Context map display updates

**Success Criteria:**
- Backward compatible with untyped edges
- New edge types validated
- Queries can filter by edge type

**Schema:**
```yaml
# Current (v2.x)
depends_on: [parent_id, other_id]

# New (v3.x) - backward compatible
depends_on:
  - parent_id                    # Generic dependency (unchanged)
  - target: auth_spec
    type: implements             # Typed edge
  - target: auth_test
    type: tested_by
```

### 8.4 Phase 4: MCP Server (v3.2.0)

**Duration:** 2-3 weeks

**Deliverables:**
1. Optional dependency (`pip install ontos[mcp]`)
2. `ontos serve` command
3. Resources: context-map, document/{id}, decision-history
4. Tools: query_dependencies, check_staleness, find_by_concept
5. Security: localhost binding, auth token
6. Documentation for MCP integration

**Success Criteria:**
- Server starts and responds to MCP protocol
- Claude Desktop can connect and use tools
- No impact on users who don't use MCP

**Command Interface:**
```bash
# Start server (foreground)
ontos serve

# Start server (background, writes PID file)
ontos serve --background

# Stop background server
ontos serve --stop

# Server status
ontos serve --status

# Custom port
ontos serve --port 8765
```

### 8.5 Phase 5: Integration Features (v3.3.0)

**Duration:** 2 weeks

**Deliverables:**
1. Detection of existing context files
2. Suggestions for integration
3. Import from CLAUDE.md (extract relevant sections)
4. Bidirectional sync exploration

**Success Criteria:**
- Ontos detects existing context files
- Provides actionable suggestions
- Doesn't break existing files

### 8.6 Timeline Summary

```
2026 Q1:
├── Week 1-3:  v3.0.0 - pip packaging
├── Week 4-5:  v3.0.1 - bug fixes, feedback
├── Week 6-7:  v3.1.0 - export formats + typed edges
└── Week 8-10: v3.2.0 - MCP server (optional)

2026 Q2:
├── v3.3.0 - integration features
├── v3.4.0 - community feedback items
└── v3.5.0 - VS Code extension (maybe)
```

---

## 9. Technical Specifications

### 9.1 Package Configuration (pyproject.toml)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ontos"
version = "3.0.0"
description = "Context-aware documentation for the agentic era"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Johnny", email = "johnny@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Documentation",
    "Topic :: Software Development :: Documentation",
]
keywords = ["documentation", "knowledge-graph", "ai", "context", "mcp"]
requires-python = ">=3.9"
dependencies = []  # Zero runtime dependencies!

[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0,<2.0.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
ontos = "ontos.cli:main"

[project.urls]
Homepage = "https://github.com/ohjona/Project-Ontos"
Documentation = "https://github.com/ohjona/Project-Ontos#readme"
Repository = "https://github.com/ohjona/Project-Ontos"
Changelog = "https://github.com/ohjona/Project-Ontos/blob/main/Ontos_CHANGELOG.md"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
ontos = ["templates/*", "hooks/*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "W", "I", "N", "UP", "B"]
```

### 9.2 CLI Architecture

```python
# ontos/cli.py
import sys
from typing import Optional

# Use argparse to maintain zero dependencies
import argparse

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ontos",
        description="Context-aware documentation for the agentic era",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize Ontos in current directory")
    init_parser.add_argument("--mode", choices=["automated", "prompted", "advisory"])
    init_parser.add_argument("--non-interactive", action="store_true")
    
    # map command
    map_parser = subparsers.add_parser("map", help="Generate context map")
    map_parser.add_argument("--strict", action="store_true")
    map_parser.add_argument("--quiet", "-q", action="store_true")
    
    # log command
    log_parser = subparsers.add_parser("log", help="Create session log")
    log_parser.add_argument("--auto", action="store_true")
    log_parser.add_argument("--enhance", "-e", action="store_true")
    
    # export command (NEW)
    export_parser = subparsers.add_parser("export", help="Export to tool-specific formats")
    export_parser.add_argument(
        "--format", "-f",
        action="append",
        choices=["claude.md", "cursor-rules", "agents.md", "copilot"],
        help="Format to export (can be repeated)"
    )
    export_parser.add_argument("--auto-sync", action="store_true")
    export_parser.add_argument("--dry-run", action="store_true")
    
    # serve command (requires MCP)
    serve_parser = subparsers.add_parser("serve", help="Start MCP server")
    serve_parser.add_argument("--port", type=int, default=0)
    serve_parser.add_argument("--background", action="store_true")
    serve_parser.add_argument("--stop", action="store_true")
    serve_parser.add_argument("--status", action="store_true")
    
    # ... other commands ...
    
    return parser

def main(argv: Optional[list[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Dispatch to command handler
    try:
        handler = get_command_handler(args.command)
        return handler(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 9.3 Export Format Specifications

#### CLAUDE.md Format

```python
# ontos/export/claude.py

CLAUDE_MD_TEMPLATE = '''# Project Context for Claude

## Overview
{overview}

## Architecture
{architecture}

## Key Documents
{key_documents}

## Recent Decisions
{recent_decisions}

## Conventions
- Use the Ontos context map for project understanding
- Reference document IDs when discussing specific components
- Check decision history for rationale behind current state
'''

def export_claude_md(context_map: dict) -> str:
    """Generate CLAUDE.md from Ontos context."""
    return CLAUDE_MD_TEMPLATE.format(
        overview=generate_overview(context_map),
        architecture=generate_architecture(context_map),
        key_documents=generate_key_documents(context_map),
        recent_decisions=generate_recent_decisions(context_map),
    )
```

#### AGENTS.md Format

```python
# ontos/export/agents.py

AGENTS_MD_TEMPLATE = '''# Agent Instructions

## Project Context
This project uses Ontos for documentation management.
See `Ontos_Context_Map.md` for the full knowledge graph.

## Tech Stack
{tech_stack}

## Key Components
{components}

## Code Guidelines
{guidelines}

## Before Making Changes
1. Check the context map for relevant documents
2. Verify dependencies won't break
3. Update session log after changes
'''

def export_agents_md(context_map: dict) -> str:
    """Generate AGENTS.md from Ontos context."""
    # Extract tech stack from atoms with 'tech' concept
    # Extract components from strategy/product docs
    # Extract guidelines from kernel docs
    pass
```

### 9.4 MCP Server Specification

```python
# ontos/mcp/server.py

from typing import Optional
import json

# Conditional import for optional dependency
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

def check_mcp_available():
    if not MCP_AVAILABLE:
        raise RuntimeError(
            "MCP support not installed. "
            "Install with: pip install ontos[mcp]"
        )

def create_server(repo_root: Optional[str] = None):
    """Create and configure the Ontos MCP server."""
    check_mcp_available()
    
    from ontos.core.context import SessionContext
    from ontos.core.paths import get_context_map_path, get_docs_dir
    
    mcp = FastMCP(
        "Ontos",
        description="Context-aware documentation for AI-native teams",
    )
    
    # Resources
    @mcp.resource("ontos://context-map")
    def get_context_map() -> str:
        """Get the full Ontos context map."""
        path = get_context_map_path()
        if not path.exists():
            return "# Context map not yet generated\nRun `ontos map` to generate."
        return path.read_text()
    
    @mcp.resource("ontos://document/{doc_id}")
    def get_document(doc_id: str) -> str:
        """Get a specific document by ID."""
        # Search for document with matching ID
        from ontos.core.frontmatter import find_document_by_id
        doc_path = find_document_by_id(doc_id)
        if not doc_path:
            return f"Document '{doc_id}' not found"
        return doc_path.read_text()
    
    @mcp.resource("ontos://decision-history")
    def get_decision_history() -> str:
        """Get the decision history ledger."""
        from ontos.core.paths import get_decision_history_path
        path = get_decision_history_path()
        if not path.exists():
            return "# No decision history\nArchive session logs to build history."
        return path.read_text()
    
    # Tools
    @mcp.tool()
    def query_dependencies(doc_id: str) -> dict:
        """Get dependencies and dependents for a document.
        
        Args:
            doc_id: The document ID to query
            
        Returns:
            Dictionary with 'depends_on' and 'dependents' lists
        """
        from ontos.commands.query import get_dependencies
        return get_dependencies(doc_id)
    
    @mcp.tool()
    def check_staleness() -> list[dict]:
        """Check for stale documentation.
        
        Returns:
            List of stale documents with details
        """
        from ontos.core.staleness import check_all_staleness
        return check_all_staleness()
    
    @mcp.tool()
    def find_by_concept(concept: str) -> list[dict]:
        """Find documents with a specific concept tag.
        
        Args:
            concept: The concept to search for
            
        Returns:
            List of matching documents
        """
        from ontos.commands.query import find_by_concept as _find
        return _find(concept)
    
    @mcp.tool()
    def validate_graph() -> dict:
        """Validate the documentation graph.
        
        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        from ontos.commands.map import validate_graph as _validate
        errors = _validate()
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @mcp.tool()
    def get_recent_logs(count: int = 5) -> list[dict]:
        """Get recent session logs.
        
        Args:
            count: Number of logs to return (default 5)
            
        Returns:
            List of recent logs with metadata
        """
        from ontos.commands.query import get_recent_logs as _get_logs
        return _get_logs(count)
    
    return mcp

def run_server(port: int = 0, host: str = "127.0.0.1"):
    """Run the MCP server."""
    server = create_server()
    server.run(host=host, port=port)
```

### 9.5 Migration Script Specification

```python
# ontos/commands/migrate_from_v2.py

import shutil
from pathlib import Path
from datetime import datetime

def migrate_from_v2(dry_run: bool = False) -> dict:
    """Migrate from v2.x file-based installation to v3.x pip package.
    
    Args:
        dry_run: If True, don't make changes, just report what would happen
        
    Returns:
        Dictionary with migration status and details
    """
    result = {
        "status": "success",
        "actions": [],
        "warnings": [],
        "errors": [],
    }
    
    ontos_dir = Path.cwd() / ".ontos"
    
    if not ontos_dir.exists():
        result["status"] = "no_installation"
        result["warnings"].append("No .ontos directory found")
        return result
    
    scripts_dir = ontos_dir / "scripts"
    if not scripts_dir.exists():
        result["status"] = "already_migrated"
        result["warnings"].append("Already appears to be v3.x installation")
        return result
    
    # Backup
    backup_dir = ontos_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not dry_run:
        shutil.copytree(ontos_dir, backup_dir)
    result["actions"].append(f"Created backup at {backup_dir}")
    
    # Remove scripts directory (now in pip package)
    if scripts_dir.exists():
        if not dry_run:
            shutil.rmtree(scripts_dir)
        result["actions"].append("Removed scripts/ directory (now in pip package)")
    
    # Update hook scripts
    hooks_dir = ontos_dir / "hooks"
    if hooks_dir.exists():
        for hook_file in hooks_dir.iterdir():
            if not dry_run:
                update_hook_script(hook_file)
            result["actions"].append(f"Updated hook: {hook_file.name}")
    
    # Check for custom config
    config_file = ontos_dir / "ontos_config.py"
    if config_file.exists():
        result["warnings"].append(
            "Custom config found at .ontos/ontos_config.py - verify compatibility"
        )
    
    return result

def update_hook_script(hook_path: Path):
    """Update hook script to use new CLI."""
    content = hook_path.read_text()
    
    # Replace old script paths with new CLI
    replacements = [
        ("python3 .ontos/scripts/ontos_pre_push_check.py", "ontos pre-push-check"),
        ("python3 .ontos/scripts/ontos_pre_commit_check.py", "ontos pre-commit-check"),
        ("python3 .ontos/scripts/ontos_end_session.py", "ontos log"),
        ("python3 .ontos/scripts/ontos_generate_context_map.py", "ontos map"),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    hook_path.write_text(content)
```

### 9.6 Schema Version 3.0

```yaml
# Document schema v3.0
---
id: example_document                  # Required: unique identifier
type: atom                            # Required: kernel|strategy|product|atom|log
status: active                        # Required: active|draft|deprecated|scaffold|pending_curation
ontos_schema: "3.0"                   # Required in v3.0+: explicit schema version

# Dependencies (enhanced with typed edges)
depends_on:                           # Optional: dependencies
  - parent_id                         # Simple dependency (backward compatible)
  - target: spec_id                   # Typed dependency
    type: implements
  - target: test_id
    type: tested_by

# Metadata
concepts: [auth, security]            # Optional: semantic tags
describes: [code_module]              # Optional: what code this describes
describes_verified: 2026-01-08        # Optional: last verification date

# Log-specific (type: log only)
event_type: feature                   # Required for logs
branch: feat/auth-refactor            # Optional: source branch
impacts: [auth_flow, api_spec]        # Optional: affected documents
---
```

### 9.7 Typed Edge Types

| Edge Type | Meaning | Example |
|-----------|---------|---------|
| `depends_on` (default) | Generic dependency | Strategy depends on kernel |
| `implements` | Implements a specification | Code implements spec |
| `tests` | Tests a component | Test file tests code |
| `tested_by` | Inverse of tests | Code tested by test file |
| `deprecates` | Supersedes another doc | v2 spec deprecates v1 spec |
| `deprecated_by` | Inverse of deprecates | v1 spec deprecated by v2 |
| `references` | Refers to for context | Blog post references spec |
| `documents` | Documents behavior | Manual documents code |

---

## 10. Code Examples and Reference Implementations

### 10.1 Complete Export Command Implementation

```python
# ontos/commands/export.py

from pathlib import Path
from typing import Optional
import json

from ontos.core.paths import get_context_map_path, PROJECT_ROOT
from ontos.core.frontmatter import parse_frontmatter
from ontos.ui.output import OutputHandler

# Format templates
FORMATS = {
    "claude.md": {
        "filename": "CLAUDE.md",
        "template": """# Project Context

## Overview
This project uses Ontos for documentation management.

{mission_section}

## Architecture
{architecture_section}

## Key Documents
{documents_section}

## Recent Decisions
{decisions_section}

## Working with This Project
- Read `Ontos_Context_Map.md` for full knowledge graph
- Reference document IDs when discussing components
- Run `ontos map` after making documentation changes
- Run `ontos log` at end of work sessions
""",
    },
    "agents.md": {
        "filename": "AGENTS.md",
        "template": """# Agent Instructions

## Project Documentation
This project uses Ontos for structured documentation.
The knowledge graph is in `Ontos_Context_Map.md`.

## Document Types
- **kernel**: Core mission and values
- **strategy**: Goals and roadmap
- **product**: Features and requirements
- **atom**: Technical specifications

## Commands
```bash
ontos map      # Regenerate context map
ontos log      # Archive session
ontos query    # Query the graph
```

## Key Components
{components_section}

## Conventions
{conventions_section}
""",
    },
    "cursor-rules": {
        "filename": ".cursorrules",
        "template": """# Cursor Rules - Generated by Ontos

## Documentation
This project uses Ontos. See Ontos_Context_Map.md.

## Context Loading
@file Ontos_Context_Map.md

## Rules
{rules_section}
""",
    },
    "copilot": {
        "filename": ".copilot-instructions.md",
        "template": """# GitHub Copilot Instructions

## Project Documentation
See `Ontos_Context_Map.md` for project knowledge graph.

## Key Information
{info_section}
""",
    },
}


def export_format(
    format_name: str,
    output: OutputHandler,
    dry_run: bool = False,
) -> Optional[Path]:
    """Export Ontos context to a specific format.
    
    Args:
        format_name: Format to export (claude.md, agents.md, etc.)
        output: OutputHandler for messages
        dry_run: If True, print but don't write
        
    Returns:
        Path to generated file, or None if dry_run
    """
    if format_name not in FORMATS:
        output.error(f"Unknown format: {format_name}")
        output.detail(f"Available formats: {', '.join(FORMATS.keys())}")
        return None
    
    format_config = FORMATS[format_name]
    template = format_config["template"]
    filename = format_config["filename"]
    
    # Gather context from Ontos documents
    context = gather_export_context()
    
    # Fill template
    content = fill_template(template, context)
    
    if dry_run:
        output.info(f"Would create {filename}:")
        print("---")
        print(content)
        print("---")
        return None
    
    # Write file
    output_path = PROJECT_ROOT / filename
    output_path.write_text(content)
    output.success(f"Created {filename}")
    
    return output_path


def gather_export_context() -> dict:
    """Gather context from Ontos documents for export."""
    context = {
        "mission": "",
        "architecture": [],
        "key_documents": [],
        "recent_decisions": [],
        "components": [],
        "conventions": [],
    }
    
    # Find mission document
    from ontos.core.paths import get_docs_dir
    docs_dir = get_docs_dir()
    
    # Scan kernel for mission
    kernel_dir = docs_dir / "kernel"
    if kernel_dir.exists():
        for md_file in kernel_dir.glob("*.md"):
            fm = parse_frontmatter(md_file)
            if fm.get("id") == "mission":
                # Extract first paragraph as mission summary
                content = md_file.read_text()
                context["mission"] = extract_summary(content)
    
    # Scan strategy for architecture
    strategy_dir = docs_dir / "strategy"
    if strategy_dir.exists():
        for md_file in strategy_dir.glob("*.md"):
            fm = parse_frontmatter(md_file)
            if fm.get("status") == "active":
                context["architecture"].append({
                    "id": fm.get("id"),
                    "title": extract_title(md_file),
                    "summary": extract_summary(md_file.read_text()),
                })
    
    # Get recent logs
    from ontos.core.paths import get_logs_dir
    logs_dir = get_logs_dir()
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("*.md"), reverse=True)[:5]
        for log_file in log_files:
            fm = parse_frontmatter(log_file)
            context["recent_decisions"].append({
                "date": extract_date_from_filename(log_file.name),
                "event_type": fm.get("event_type", "chore"),
                "summary": extract_summary(log_file.read_text()),
            })
    
    return context


def fill_template(template: str, context: dict) -> str:
    """Fill template with context."""
    sections = {}
    
    # Mission section
    if context.get("mission"):
        sections["mission_section"] = f"### Mission\n{context['mission']}"
    else:
        sections["mission_section"] = ""
    
    # Architecture section
    if context.get("architecture"):
        lines = ["### Strategy Documents"]
        for doc in context["architecture"]:
            lines.append(f"- **{doc['id']}**: {doc['summary'][:100]}...")
        sections["architecture_section"] = "\n".join(lines)
    else:
        sections["architecture_section"] = "See Ontos_Context_Map.md"
    
    # Documents section
    sections["documents_section"] = "See Ontos_Context_Map.md for full index"
    
    # Decisions section
    if context.get("recent_decisions"):
        lines = ["### Recent Sessions"]
        for decision in context["recent_decisions"][:5]:
            lines.append(f"- [{decision['event_type']}] {decision['summary'][:80]}...")
        sections["decisions_section"] = "\n".join(lines)
    else:
        sections["decisions_section"] = "No recent sessions archived"
    
    # Components section
    sections["components_section"] = "See Ontos_Context_Map.md"
    
    # Conventions section
    sections["conventions_section"] = "- Follow existing patterns\n- Update docs when changing code"
    
    # Rules section
    sections["rules_section"] = "- Check Ontos_Context_Map.md before major changes"
    
    # Info section
    sections["info_section"] = "Documentation managed by Ontos"
    
    # Fill template
    for key, value in sections.items():
        template = template.replace(f"{{{key}}}", value)
    
    return template


def extract_summary(content: str, max_length: int = 200) -> str:
    """Extract summary from markdown content."""
    lines = content.split("\n")
    
    # Skip frontmatter
    in_frontmatter = False
    summary_lines = []
    
    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if line.startswith("#"):
            continue
        if line.strip():
            summary_lines.append(line.strip())
            if len(" ".join(summary_lines)) > max_length:
                break
    
    summary = " ".join(summary_lines)
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."
    
    return summary


def extract_title(file_path: Path) -> str:
    """Extract title from markdown file."""
    content = file_path.read_text()
    for line in content.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return file_path.stem


def extract_date_from_filename(filename: str) -> str:
    """Extract date from log filename like log_20260108_feature_x.md"""
    parts = filename.split("_")
    if len(parts) >= 2 and parts[0] == "log":
        return parts[1]
    return "unknown"
```

### 10.2 Complete MCP Server with Auth

```python
# ontos/mcp/server.py

import os
import secrets
from pathlib import Path
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class OntosMCPServer:
    """MCP server for Ontos context."""
    
    TOKEN_FILE = Path.home() / ".ontos" / "mcp_token"
    PID_FILE = Path.home() / ".ontos" / "mcp.pid"
    PORT_FILE = Path.home() / ".ontos" / "mcp.port"
    
    def __init__(self, repo_root: Optional[Path] = None):
        if not MCP_AVAILABLE:
            raise RuntimeError(
                "MCP not installed. Run: pip install ontos[mcp]"
            )
        
        self.repo_root = repo_root or Path.cwd()
        self.mcp = self._create_server()
        self._ensure_token()
    
    def _ensure_token(self):
        """Ensure auth token exists."""
        self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not self.TOKEN_FILE.exists():
            token = secrets.token_urlsafe(32)
            self.TOKEN_FILE.write_text(token)
            self.TOKEN_FILE.chmod(0o600)  # Owner read/write only
    
    def get_token(self) -> str:
        """Get the auth token."""
        return self.TOKEN_FILE.read_text().strip()
    
    def _create_server(self) -> FastMCP:
        """Create and configure the MCP server."""
        mcp = FastMCP(
            "Ontos",
            description="Context-aware documentation system",
        )
        
        self._register_resources(mcp)
        self._register_tools(mcp)
        
        return mcp
    
    def _register_resources(self, mcp: FastMCP):
        """Register MCP resources."""
        repo_root = self.repo_root
        
        @mcp.resource("ontos://context-map")
        def get_context_map() -> str:
            """Full Ontos context map."""
            from ontos.core.paths import get_context_map_path
            path = get_context_map_path()
            if path.exists():
                return path.read_text()
            return "# No context map\nRun `ontos map` to generate."
        
        @mcp.resource("ontos://document/{doc_id}")
        def get_document(doc_id: str) -> str:
            """Get document by ID."""
            from ontos.core.frontmatter import find_document_by_id
            doc = find_document_by_id(doc_id, repo_root)
            if doc:
                return doc.read_text()
            return f"Document '{doc_id}' not found"
        
        @mcp.resource("ontos://decision-history")
        def get_history() -> str:
            """Decision history ledger."""
            from ontos.core.paths import get_decision_history_path
            path = get_decision_history_path()
            if path.exists():
                return path.read_text()
            return "# No history\nArchive sessions to build history."
        
        @mcp.resource("ontos://schema")
        def get_schema() -> str:
            """Current Ontos schema documentation."""
            return '''# Ontos Schema v3.0

## Document Types
- kernel: Mission, values, principles
- strategy: Goals, roadmap, audience
- product: Features, requirements
- atom: Technical specifications
- log: Session history

## Required Fields
- id: Unique identifier (snake_case)
- type: Document type
- status: active|draft|deprecated|scaffold|pending_curation
- ontos_schema: "3.0"

## Optional Fields
- depends_on: List of dependencies
- concepts: List of semantic tags
- describes: List of code it describes
- describes_verified: Last verification date
'''
    
    def _register_tools(self, mcp: FastMCP):
        """Register MCP tools."""
        repo_root = self.repo_root
        
        @mcp.tool()
        def query_dependencies(doc_id: str) -> dict:
            """Get dependencies and dependents for a document."""
            from ontos.commands.query import get_dependencies
            result = get_dependencies(doc_id, repo_root)
            return {
                "doc_id": doc_id,
                "depends_on": result.get("depends_on", []),
                "dependents": result.get("dependents", []),
                "depth": result.get("depth", 0),
            }
        
        @mcp.tool()
        def check_staleness() -> list:
            """Check for stale documentation."""
            from ontos.core.staleness import check_all_staleness
            stale = check_all_staleness(repo_root)
            return [
                {
                    "doc_id": s.doc_id,
                    "describes": s.atom_id,
                    "verified": str(s.verified_date),
                    "atom_modified": str(s.atom_modified),
                    "days_stale": s.days_stale,
                }
                for s in stale
            ]
        
        @mcp.tool()
        def find_by_concept(concept: str) -> list:
            """Find documents with a concept tag."""
            from ontos.commands.query import find_documents_by_concept
            docs = find_documents_by_concept(concept, repo_root)
            return [
                {"id": d.id, "type": d.type, "path": str(d.path)}
                for d in docs
            ]
        
        @mcp.tool()
        def validate_graph() -> dict:
            """Validate the documentation graph."""
            from ontos.commands.map import run_validation
            errors = run_validation(repo_root)
            return {
                "valid": len(errors) == 0,
                "error_count": len(errors),
                "errors": [
                    {"type": e.error_type, "message": e.message, "doc_id": e.doc_id}
                    for e in errors[:20]  # Limit to first 20
                ],
            }
        
        @mcp.tool()
        def get_recent_logs(count: int = 5) -> list:
            """Get recent session logs."""
            from ontos.commands.query import get_recent_logs as _get_logs
            logs = _get_logs(count, repo_root)
            return [
                {
                    "id": log.id,
                    "date": log.date,
                    "event_type": log.event_type,
                    "summary": log.summary[:200],
                    "impacts": log.impacts,
                }
                for log in logs
            ]
        
        @mcp.tool()
        def regenerate_map() -> dict:
            """Regenerate the context map."""
            from ontos.commands.map import generate_map
            result = generate_map(repo_root)
            return {
                "success": result.success,
                "documents_scanned": result.doc_count,
                "errors": result.error_count,
                "path": str(result.output_path),
            }
    
    def run(self, host: str = "127.0.0.1", port: int = 0):
        """Run the MCP server."""
        import socket
        
        # Find available port if 0
        if port == 0:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, 0))
                port = s.getsockname()[1]
        
        # Save port for clients
        self.PORT_FILE.write_text(str(port))
        
        # Save PID
        self.PID_FILE.write_text(str(os.getpid()))
        
        print(f"Ontos MCP Server starting on {host}:{port}")
        print(f"Auth token: {self.get_token()[:8]}...")
        print(f"Connect with: ontos://localhost:{port}")
        
        try:
            self.mcp.run(host=host, port=port)
        finally:
            # Cleanup
            self.PID_FILE.unlink(missing_ok=True)
            self.PORT_FILE.unlink(missing_ok=True)
    
    @classmethod
    def get_server_info(cls) -> Optional[dict]:
        """Get running server info, if any."""
        if not cls.PID_FILE.exists():
            return None
        
        pid = int(cls.PID_FILE.read_text().strip())
        port = int(cls.PORT_FILE.read_text().strip()) if cls.PORT_FILE.exists() else None
        
        # Check if process is alive
        try:
            os.kill(pid, 0)
            return {"pid": pid, "port": port, "running": True}
        except OSError:
            # Process not running, clean up stale files
            cls.PID_FILE.unlink(missing_ok=True)
            cls.PORT_FILE.unlink(missing_ok=True)
            return None
    
    @classmethod
    def stop_server(cls) -> bool:
        """Stop running server."""
        info = cls.get_server_info()
        if not info:
            return False
        
        try:
            os.kill(info["pid"], 15)  # SIGTERM
            cls.PID_FILE.unlink(missing_ok=True)
            cls.PORT_FILE.unlink(missing_ok=True)
            return True
        except OSError:
            return False


def main():
    """CLI entry point for MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ontos MCP Server")
    parser.add_argument("--port", type=int, default=0, help="Port to listen on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--status", action="store_true", help="Show server status")
    parser.add_argument("--stop", action="store_true", help="Stop running server")
    
    args = parser.parse_args()
    
    if args.status:
        info = OntosMCPServer.get_server_info()
        if info:
            print(f"Server running: PID {info['pid']}, port {info['port']}")
        else:
            print("No server running")
        return
    
    if args.stop:
        if OntosMCPServer.stop_server():
            print("Server stopped")
        else:
            print("No server to stop")
        return
    
    server = OntosMCPServer()
    server.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

### 10.3 Integration Test Example

```python
# tests/test_mcp_server.py

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Skip if MCP not available
pytest.importorskip("mcp")

from ontos.mcp.server import OntosMCPServer


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary Ontos repository."""
    # Create .ontos directory
    ontos_dir = tmp_path / ".ontos"
    ontos_dir.mkdir()
    
    # Create docs structure
    docs_dir = tmp_path / "docs"
    kernel_dir = docs_dir / "kernel"
    kernel_dir.mkdir(parents=True)
    
    # Create mission doc
    mission = kernel_dir / "mission.md"
    mission.write_text('''---
id: mission
type: kernel
status: active
ontos_schema: "3.0"
---

# Mission

Test mission statement.
''')
    
    # Create context map
    context_map = tmp_path / "Ontos_Context_Map.md"
    context_map.write_text('''# Ontos Context Map

## Hierarchy
- mission (kernel)
''')
    
    return tmp_path


class TestOntosMCPServer:
    
    def test_server_creation(self, temp_repo):
        """Server can be created with repo root."""
        server = OntosMCPServer(repo_root=temp_repo)
        assert server.mcp is not None
    
    def test_token_generation(self, temp_repo):
        """Server generates auth token."""
        server = OntosMCPServer(repo_root=temp_repo)
        token = server.get_token()
        assert len(token) > 20
        
        # Token persists
        token2 = server.get_token()
        assert token == token2
    
    def test_context_map_resource(self, temp_repo):
        """Context map resource returns content."""
        server = OntosMCPServer(repo_root=temp_repo)
        
        # Access resource directly
        resources = server.mcp._resources
        context_map = resources["ontos://context-map"]()
        
        assert "Ontos Context Map" in context_map
        assert "mission" in context_map
    
    def test_query_dependencies_tool(self, temp_repo):
        """Query dependencies tool works."""
        server = OntosMCPServer(repo_root=temp_repo)
        
        # Access tool directly
        tools = server.mcp._tools
        result = tools["query_dependencies"](doc_id="mission")
        
        assert result["doc_id"] == "mission"
        assert "depends_on" in result
        assert "dependents" in result
    
    def test_validate_graph_tool(self, temp_repo):
        """Validate graph tool returns results."""
        server = OntosMCPServer(repo_root=temp_repo)
        
        tools = server.mcp._tools
        result = tools["validate_graph"]()
        
        assert "valid" in result
        assert "errors" in result
    
    def test_server_info_when_not_running(self):
        """Server info returns None when not running."""
        info = OntosMCPServer.get_server_info()
        assert info is None


class TestExportCommand:
    """Test export command functionality."""
    
    def test_export_claude_md(self, temp_repo):
        """Export to CLAUDE.md format."""
        from ontos.commands.export import export_format
        from ontos.ui.output import OutputHandler
        
        output = OutputHandler(quiet=True)
        
        with patch("ontos.core.paths.PROJECT_ROOT", temp_repo):
            result = export_format("claude.md", output, dry_run=True)
        
        # Dry run returns None
        assert result is None
    
    def test_export_agents_md(self, temp_repo):
        """Export to AGENTS.md format."""
        from ontos.commands.export import export_format
        from ontos.ui.output import OutputHandler
        
        output = OutputHandler(quiet=True)
        
        with patch("ontos.core.paths.PROJECT_ROOT", temp_repo):
            result = export_format("agents.md", output, dry_run=False)
        
        assert result is not None
        assert result.name == "AGENTS.md"
        assert result.exists()
```

---

## 11. Decision Framework

### 11.1 Decision: Default Installation Experience

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | CLI only (no daemon) | Simple, lightweight, fast | No dynamic queries |
| B | Daemon required | Rich features | Complexity, resources |
| C | CLI default, daemon optional | Best of both | Two code paths |

**Recommendation:** Option C

**Rationale:**
- Honors "lightweight" value
- Enables power users
- No forced complexity
- MCP adoption not required

### 11.2 Decision: Package Structure

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | Single package | Simpler distribution | MCP deps always present |
| B | Two packages | Clean separation | Two packages to maintain |
| C | Optional deps | Single package, optional MCP | Slightly complex install |

**Recommendation:** Option C

**Rationale:**
- `pip install ontos` stays lightweight
- `pip install ontos[mcp]` enables MCP
- One codebase, one version
- Standard Python pattern

### 11.3 Decision: Export vs. MCP Priority

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | MCP first | Aligns with ecosystem | Complexity, limited users |
| B | Export first | Immediate value, low risk | Less "innovative" |
| C | Both simultaneously | Complete solution | More work, risk |

**Recommendation:** Option B

**Rationale:**
- Export provides value without MCP adoption
- Lower implementation risk
- Works with ALL tools, not just MCP-aware
- Can ship faster

### 11.4 Decision: Breaking Changes Policy

**Question:** How to handle v2.x → v3.0 breaking changes?

**Policy:**
1. Schema changes use versioning (already in place)
2. CLI changes use deprecation warnings (already in place)
3. Migration tooling provided (`ontos migrate-from-v2`)
4. Minimum 1 minor version with deprecation before removal
5. Clear changelog documentation

### 11.5 Decision: MCP Security Model

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | No auth (localhost only) | Simple | Risk if port exposed |
| B | Token auth | Standard, secure | Token management |
| C | mTLS | Enterprise-grade | Complexity |

**Recommendation:** Option B (Token auth with localhost binding)

**Rationale:**
- Localhost binding prevents remote access
- Token prevents local process spoofing
- Simple to implement
- Can upgrade to mTLS later if needed

---

## 12. Appendices

### 12.1 Glossary

| Term | Definition |
|------|------------|
| Atom | Technical documentation (implementation details) |
| Curation Level | L0 (scaffold), L1 (stub), L2 (full) |
| Daemon | Long-running background process |
| Decision History | Immutable ledger of archived session decisions |
| Depends On | Explicit dependency relationship |
| Edge (typed) | Relationship with semantic meaning (implements, tests) |
| Impacts | Documents affected by a session |
| Kernel | Core documentation (mission, values) |
| Knowledge Graph | Structured documentation with relationships |
| MCP | Model Context Protocol |
| Product | Feature documentation |
| Resource (MCP) | Data exposed for reading |
| Schema | Frontmatter structure specification |
| Session Log | Record of work in a development session |
| Space | Current truth (kernel, strategy, product, atom) |
| Staleness | Documentation outdated relative to code |
| Strategy | Goals and roadmap documentation |
| Time | Historical record (logs, decisions) |
| Tool (MCP) | Function exposed for calling |

### 12.2 References

**MCP Specification:**
- https://modelcontextprotocol.io/specification/2025-06-18
- https://github.com/modelcontextprotocol/python-sdk

**Python Packaging:**
- https://packaging.python.org/en/latest/
- https://peps.python.org/pep-0621/ (pyproject.toml)

**Context File Formats:**
- CLAUDE.md: https://docs.anthropic.com/en/docs/claude-code
- AGENTS.md: Emerging standard (no formal spec yet)
- .cursorrules: https://docs.cursor.com/context/rules-for-ai

### 12.3 Version Comparison Table

| Feature | v2.9.5 | v3.0.0 | v3.1.0 | v3.2.0 |
|---------|--------|--------|--------|--------|
| Distribution | install.py | pip | pip | pip |
| Dependencies | 0 | 0 | 0 | 0 (core) |
| MCP | - | - | - | Optional |
| Export formats | - | - | Yes | Yes |
| Typed edges | - | - | Yes | Yes |
| Schema version | 2.2 | 3.0 | 3.0 | 3.0 |

### 12.4 Migration Checklist (v2.x → v3.0)

- [ ] Backup existing `.ontos/` directory
- [ ] Install pip package: `pip install ontos`
- [ ] Run migration: `ontos migrate-from-v2`
- [ ] Verify hooks updated
- [ ] Test CLI commands work
- [ ] Update any custom scripts
- [ ] Run `ontos map` to verify
- [ ] Remove old `.ontos/scripts/` if present

### 12.5 Sample pyproject.toml (Complete)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ontos"
version = "3.0.0"
description = "Context-aware documentation for the agentic era"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Johnny"}
]
maintainers = [
    {name = "Johnny"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Documentation",
    "Topic :: Software Development :: Documentation",
    "Topic :: Software Development :: Version Control :: Git",
]
keywords = [
    "documentation",
    "knowledge-graph",
    "ai",
    "context",
    "mcp",
    "llm",
    "developer-tools",
]
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0,<2.0.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
]

[project.scripts]
ontos = "ontos.cli:main"

[project.urls]
Homepage = "https://github.com/ohjona/Project-Ontos"
Documentation = "https://github.com/ohjona/Project-Ontos#readme"
Repository = "https://github.com/ohjona/Project-Ontos"
Changelog = "https://github.com/ohjona/Project-Ontos/blob/main/Ontos_CHANGELOG.md"
"Bug Tracker" = "https://github.com/ohjona/Project-Ontos/issues"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
ontos = [
    "templates/*.template",
    "templates/*.md",
    "hooks/*",
    "py.typed",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow",
    "mcp: marks tests requiring MCP",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src/ontos"]
branch = true
omit = ["*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true
namespace_packages = true
explicit_package_bases = true

[[tool.mypy.overrides]]
module = ["mcp.*"]
ignore_missing_imports = true

[tool.ruff]
line-length = 100
target-version = "py39"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "W",   # pycodestyle warnings
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DTZ", # flake8-datetimez
    "T10", # flake8-debugger
    "ISC", # flake8-implicit-str-concat
    "PIE", # flake8-pie
    "PT",  # flake8-pytest-style
    "RSE", # flake8-raise
    "RET", # flake8-return
    "SIM", # flake8-simplify
    "ARG", # flake8-unused-arguments
    "PTH", # flake8-use-pathlib
    "ERA", # eradicate
    "PL",  # pylint
    "RUF", # ruff-specific
]
ignore = [
    "PLR0913",  # too many arguments
    "PLR2004",  # magic value comparison
]

[tool.ruff.lint.isort]
known-first-party = ["ontos"]

[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311", "py312"]
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Technical Co-Founder | Initial comprehensive analysis |

---

*End of document. Total: ~15,000 words, ~22,000 tokens.*
