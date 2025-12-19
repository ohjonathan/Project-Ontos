---
id: common_concepts
type: atom
status: active
depends_on: []
---

# Common Concepts

Reference vocabulary for `concepts` field in Session Logs.

## Usage

When tagging a log, check this list first. Use existing terms over synonyms to ensure graph connectivity.

**Example:**
```yaml
# Good - uses standard vocabulary
concepts: [auth, api, db]

# Bad - creates orphan nodes in the graph
concepts: [authentication, endpoints, database-stuff]
```

---

## Vocabulary

### Core Domains

| Concept | Covers | Avoid Using |
|:--------|:-------|:------------|
| `auth` | Authentication, authorization, login, identity, OAuth, JWT | `authentication`, `login`, `identity`, `oauth` |
| `api` | Endpoints, REST, GraphQL, routes, controllers | `endpoints`, `routes`, `rest`, `graphql` |
| `db` | Database, storage, SQL, queries, migrations | `database`, `storage`, `sql`, `postgres` |
| `ui` | Frontend, components, CSS, styling, layout | `frontend`, `components`, `styling`, `css` |
| `schema` | Data models, types, validation, structure | `models`, `types`, `validation`, `data-model` |

### Process Domains

| Concept | Covers | Avoid Using |
|:--------|:-------|:------------|
| `devops` | CI/CD, deployment, hosting, Docker, infrastructure | `deployment`, `ci`, `infrastructure`, `docker` |
| `testing` | Unit tests, integration tests, QA, test coverage | `tests`, `qa`, `test`, `unit-tests` |
| `perf` | Performance, optimization, caching, speed | `performance`, `optimization`, `speed`, `caching` |
| `security` | Vulnerabilities, encryption, access control, secrets | `vulnerabilities`, `encryption`, `secrets` |
| `docs` | Documentation, guides, references, READMEs | `documentation`, `guides`, `readme` |

### Workflow

| Concept | Covers |
|:--------|:-------|
| `cleanup` | Refactoring, dead code removal, organization |
| `config` | Configuration, settings, environment variables |
| `workflow` | Process changes, rituals, automation |

### Documentation Tracking (v2.7)

| Concept | Covers |
|:--------|:-------|
| `describes` | Documentation relationship tracking — marks which atoms a doc describes |
| `staleness` | Detection of outdated documentation when described atoms change |
| `immutable-history` | Auto-generated decision_history.md from session logs |

---

## Adding New Concepts

If no existing concept fits:

1. **Check first** — Can a broader existing concept work?
2. **Be conservative** — Fewer concepts with clear scope > many overlapping concepts
3. **Follow conventions:**
   - Lowercase
   - Single words preferred
   - Hyphens for multi-word (`data-model` not `dataModel`)
4. **Document it** — Add to this file with clear scope
5. **Update existing logs** — If applicable to past work

---

## Why This Matters (v3.0)

This vocabulary enables subgraph queries:

```bash
# Future capability (v3.0)
python3 .ontos/scripts/ontos_query.py --concept auth --hops 2
```

**Consistent tagging now = accurate retrieval later.**
