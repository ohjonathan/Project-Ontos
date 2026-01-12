"""
Commands module - High-level command orchestration.

This module contains command implementations that orchestrate
core logic and I/O operations. Commands may import from all layers.

Phase 2 modules:
- map.py: Context map generation orchestration
- log.py: Session log creation orchestration
- verify.py: Document verification (wrapper)
- query.py: Document query (wrapper)
- migrate.py: Schema migration (wrapper)
- consolidate.py: Log consolidation (wrapper)
- promote.py: Proposal promotion (wrapper)
- scaffold.py: Document scaffolding (wrapper)
- stub.py: Stub creation (wrapper)

Note: Wrapper modules delegate to bundled scripts for behavioral parity.
Full native implementations will be completed in Phase 4.
"""

# Primary orchestration modules (Phase 2 native)
from ontos.commands.map import (
    GenerateMapOptions,
    generate_context_map,
)

from ontos.commands.log import (
    EndSessionOptions,
    create_session_log,
    suggest_session_impacts,
    validate_session_concepts,
)

# Wrapper modules (delegate to bundled scripts)
# These provide the new module API while maintaining behavioral parity

# verify - Document verification
from ontos.commands.verify import (
    verify_document,
    find_stale_documents,
    verify_all_interactive,
)

# query - Document query
from ontos.commands.query import (
    query_documents,
    get_document_by_id,
)

# migrate - Schema migration
from ontos.commands.migrate import (
    migrate_schema,
    check_schema_version,
)

# consolidate - Log consolidation
from ontos.commands.consolidate import (
    consolidate_logs,
    get_consolidation_candidates,
)

# promote - Proposal promotion
from ontos.commands.promote import (
    promote_proposal,
    find_promotable_proposals,
)

# scaffold - Document scaffolding
from ontos.commands.scaffold import (
    scaffold_document,
    get_available_templates,
)

# stub - Stub creation
from ontos.commands.stub import (
    create_stub,
    create_stubs_for_missing,
)

__all__ = [
    # Native orchestration (Phase 2)
    "GenerateMapOptions",
    "generate_context_map",
    "EndSessionOptions",
    "create_session_log",
    "suggest_session_impacts",
    "validate_session_concepts",
    # Wrappers (Phase 2, full impl Phase 4)
    "verify_document",
    "find_stale_documents",
    "verify_all_interactive",
    "query_documents",
    "get_document_by_id",
    "migrate_schema",
    "check_schema_version",
    "consolidate_logs",
    "get_consolidation_candidates",
    "promote_proposal",
    "find_promotable_proposals",
    "scaffold_document",
    "get_available_templates",
    "create_stub",
    "create_stubs_for_missing",
]
