---
id: s3_archive_analysis
type: strategy
status: draft
depends_on: [v2_strategy]
concepts: [architecture, s3, archive]
---

# S3 Archive Integration Analysis

**Date:** 2025-12-16
**Author:** Claude Code

---

## Executive Summary

This document analyzes two options for integrating AWS S3 into the Ontos archiving system, comparing them across performance, security, cost, and user convenience dimensions.

---

## Current Architecture Context

### Key Insight: Indirection Layer

The current system uses `decision_history.md` as an **indirection layer** for archive access:

```
Agent Query: "Why did we choose OAuth2?"
    ↓
1. Read decision_history.md (lookup table)
    ↓
2. Find entry: "2025-12-10 | auth | archive/logs/2025-12-10_auth.md"
    ↓
3. Read file at Archive Path
    ↓
4. Return synthesized answer
```

**Archives are NEVER discovered via filesystem scanning** - they're always accessed through the decision ledger. This makes S3 migration architecturally clean.

### Current Archive Behavior

| Aspect | Current State |
|--------|---------------|
| Context map generation | Skips `archive/` directory entirely |
| Active log count | ~15 logs before consolidation warning |
| Archive access frequency | Low - only on historical recall queries |
| Archive growth | ~17 files / 341 KB currently |

---

## Option A: Consolidation Only → S3

**Active logs stay local in `docs/logs/`; only old logs (30+ days) go to S3**

```
docs/logs/
├── 2025-12-15_feature-x.md   ← Active (local)
├── 2025-12-14_bugfix-y.md    ← Active (local)
└── ...

s3://user-bucket/ontos/archive/
├── 2025-11-01_old-feature.md ← Archived (S3)
└── ...
```

### Performance Analysis

| Operation | Impact | Notes |
|-----------|--------|-------|
| **Context map generation** | ✅ No impact | Archives already excluded from scanning |
| **Session logging** | ✅ No impact | New logs still written locally |
| **Consolidation (write)** | ⚠️ ~500ms-2s per file | S3 PutObject instead of `shutil.move()` |
| **Historical recall (read)** | ⚠️ ~200-500ms per file | S3 GetObject vs local disk read |
| **Knowledge graph queries** | ✅ No impact | Queries operate on active files only |

**Latency breakdown:**
- Local file read: ~1-5ms
- S3 GetObject (same region): ~50-200ms
- S3 GetObject (cross-region): ~200-500ms

### Security Analysis

| Aspect | Assessment |
|--------|------------|
| **Credential exposure** | Low - credentials only needed during consolidation |
| **Attack surface** | Minimal - S3 access is write-once, read-rarely |
| **Data at rest** | S3 encryption available (SSE-S3, SSE-KMS) |
| **Blast radius** | Limited - only archived (old) data exposed |

### Cost Analysis

| Cost Factor | Estimate |
|-------------|----------|
| **S3 Storage** | ~$0.023/GB/month (S3 Standard) |
| **PUT requests** | ~$0.005 per 1,000 requests |
| **GET requests** | ~$0.0004 per 1,000 requests |
| **Estimated monthly** | < $0.10 for typical usage (< 1GB archives) |

### User Convenience

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Setup complexity** | ⭐⭐⭐⭐ Good | Only configure S3 for consolidation |
| **Daily workflow** | ⭐⭐⭐⭐⭐ Excellent | No change to session logging |
| **Offline access** | ⭐⭐⭐⭐⭐ Excellent | Active logs always available locally |
| **Historical recall** | ⭐⭐⭐ Moderate | Requires network for old logs |

---

## Option B: All Archives → S3

**Both session logs AND consolidated archives go to S3**

```
s3://user-bucket/ontos/
├── logs/
│   ├── 2025-12-15_feature-x.md   ← Active (S3)
│   └── 2025-12-14_bugfix-y.md    ← Active (S3)
└── archive/
    └── 2025-11-01_old-feature.md ← Archived (S3)
```

### Performance Analysis

| Operation | Impact | Notes |
|-----------|--------|-------|
| **Context map generation** | ⚠️ Requires S3 ListObjects | Must fetch file list from S3 |
| **Session logging** | ⚠️ ~500ms-2s per log | S3 PutObject on every session end |
| **Consolidation (write)** | ⚠️ S3→S3 copy | CopyObject + DeleteObject |
| **Historical recall (read)** | ⚠️ ~200-500ms per file | Same as Option A |
| **Knowledge graph queries** | ❌ Major impact | Every query requires S3 reads |

**Critical issue:** Context map generation currently uses `os.walk()` to scan `docs/logs/`. With S3:
- Must use S3 ListObjectsV2 to enumerate files
- Must use S3 GetObject to read frontmatter for each file
- Scanning 15 active logs: ~15 × 200ms = ~3 seconds (vs ~50ms local)

### Security Analysis

| Aspect | Assessment |
|--------|------------|
| **Credential exposure** | High - credentials needed for all operations |
| **Attack surface** | Large - S3 access on every session |
| **Data at rest** | S3 encryption available |
| **Blast radius** | High - all logs (including recent work) exposed |

### Cost Analysis

| Cost Factor | Estimate |
|-------------|----------|
| **S3 Storage** | ~$0.023/GB/month |
| **PUT requests** | Higher - every session creates a log |
| **GET requests** | Much higher - context map reads all logs |
| **LIST requests** | Added cost for scanning |
| **Estimated monthly** | ~$0.50-2.00 depending on activity |

### User Convenience

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Setup complexity** | ⭐⭐ Poor | Must configure S3 for all operations |
| **Daily workflow** | ⭐⭐ Poor | Every session end requires network |
| **Offline access** | ⭐ Very Poor | Cannot work without network |
| **Historical recall** | ⭐⭐⭐ Moderate | Same as Option A |

---

## Comparison Matrix

| Dimension | Option A (Consolidation Only) | Option B (All Archives) |
|-----------|------------------------------|------------------------|
| **Context map speed** | ✅ Unchanged (~50ms) | ❌ Degraded (~3s+) |
| **Session logging speed** | ✅ Unchanged (~10ms) | ⚠️ Slower (~500ms-2s) |
| **Offline capability** | ✅ Full (active logs local) | ❌ None |
| **Credential exposure** | ⭐⭐⭐⭐ Low | ⭐⭐ High |
| **Monthly cost** | ⭐⭐⭐⭐⭐ ~$0.10 | ⭐⭐⭐ ~$0.50-2.00 |
| **Setup complexity** | ⭐⭐⭐⭐ Simple | ⭐⭐ Complex |
| **Code changes required** | ⭐⭐⭐⭐ Minimal | ⭐ Extensive |

---

## MCP Integration for Credentials

### Recommended Approach

Use an existing MCP server for S3 operations rather than implementing boto3 directly:

**Option 1: AWS Labs Official (awslabs/mcp)**
- Repository: https://github.com/awslabs/mcp
- Pros: Official AWS support, well-maintained
- Cons: Focused on S3 Tables, may be overkill

**Option 2: khuynh22/aws-s3-mcp-server (Recommended)**
- Repository: https://github.com/khuynh22/aws-s3-mcp-server
- Pros: Pre-signed URLs (more secure), simple operations
- Cons: Community-maintained

**Option 3: samuraikun/aws-s3-mcp**
- Repository: https://github.com/samuraikun/aws-s3-mcp
- Pros: STDIO + HTTP transport, streaming support
- Cons: Community-maintained

### Authentication Flow with MCP

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Environment                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ~/.aws/credentials         MCP Server Config               │
│  ┌──────────────────┐       ┌──────────────────────────┐   │
│  │ [default]        │       │ "s3": {                  │   │
│  │ aws_access_key=  │──────▶│   "command": "npx",      │   │
│  │ aws_secret_key=  │       │   "args": ["s3-mcp"],    │   │
│  │ region=          │       │   "env": {               │   │
│  └──────────────────┘       │     "AWS_PROFILE": "..." │   │
│                             │   }                      │   │
│         OR                  │ }                        │   │
│                             └──────────────────────────┘   │
│  Environment Variables                    │                 │
│  ┌──────────────────┐                     │                 │
│  │ AWS_ACCESS_KEY_ID│                     ▼                 │
│  │ AWS_SECRET_...   │            ┌────────────────┐        │
│  │ AWS_REGION       │            │  MCP Server    │        │
│  └──────────────────┘            │  (s3-mcp)      │        │
│                                  └───────┬────────┘        │
│                                          │                  │
│                                          ▼                  │
│                                  ┌────────────────┐        │
│                                  │   AWS S3 API   │        │
│                                  └────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

**Key benefits of MCP approach:**
1. Ontos scripts don't handle credentials directly
2. User configures MCP server once in their Claude Code settings
3. Credentials never appear in Ontos codebase or logs
4. Supports IAM roles, profiles, and environment variables

---

## Fallback Behavior Design

### Failure Scenarios

| Scenario | Detection | Fallback |
|----------|-----------|----------|
| MCP server not configured | Tool call fails | Archive locally + warn |
| S3 bucket doesn't exist | PutObject fails | Archive locally + warn |
| Permission denied | 403 error | Archive locally + warn |
| Network timeout | Timeout error | Archive locally + warn |
| Partial upload | Incomplete | Retry once, then local + warn |

### Warning Persistence

When S3 fails, record the failure:

```python
# .ontos/s3_failures.json
{
  "last_failure": "2025-12-16T10:30:00Z",
  "failure_reason": "S3 bucket not accessible",
  "pending_uploads": [
    "docs/archive/2025-12-15_feature.md",
    "docs/archive/2025-12-14_bugfix.md"
  ]
}
```

### Console Warning

On every Ontos operation (consolidation, session end, context map):

```
⚠️  S3 INTEGRATION DEGRADED
    Last failure: 2025-12-16 10:30 UTC
    Reason: S3 bucket not accessible
    Pending uploads: 2 files

    Archives are being saved locally. Run 'ontos s3-sync' to retry.
```

---

## Recommendation

**Option A (Consolidation Only → S3)** is strongly recommended because:

1. **Zero impact on daily workflow** - Session logging unchanged
2. **Maintains offline capability** - Active logs always local
3. **Minimal code changes** - Only modify `ontos_consolidate.py`
4. **Lower security exposure** - Credentials only used during consolidation
5. **Better cost profile** - Fewer S3 operations
6. **Graceful degradation** - Falls back to local archive seamlessly

Option B would require significant architectural changes to context map generation and would break offline workflows entirely.

---

## Next Steps

1. Finalize credential handling approach (MCP vs direct boto3)
2. Design configuration schema for S3 bucket settings
3. Implement fallback behavior with warning persistence
4. Update decision_history.md path format for S3 URLs
5. Write user documentation for S3 setup

