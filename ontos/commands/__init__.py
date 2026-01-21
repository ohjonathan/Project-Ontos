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

Phase 3 modules:
- init.py: Project initialization

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

# Phase 3: Init command
from ontos.commands.init import (
    InitOptions,
    init_command,
    ONTOS_HOOK_MARKER,
)

# Phase 4: New commands
from ontos.commands.doctor import (
    DoctorOptions,
    DoctorResult,
    CheckResult,
    doctor_command,
    format_doctor_output,
)

from ontos.commands.hook import (
    HookOptions,
    hook_command,
)

from ontos.commands.export import (
    ExportOptions,
    export_command,
)

# Wrapper modules (delegate to bundled scripts)
# These provide the new module API while maintaining behavioral parity

# verify - Document verification
from ontos.commands.verify import (
    verify_command,
    VerifyOptions,
    verify_document,
    find_stale_documents_list,
)

# query - Document query
from ontos.commands.query import (
    query_command,
    QueryOptions,
    scan_docs_for_query,
)

# migrate - Schema migration
from ontos.commands.migrate import (
    migrate_command,
    MigrateOptions,
)

# consolidate - Log consolidation
from ontos.commands.consolidate import (
    consolidate_command,
    ConsolidateOptions,
)

# promote - Proposal promotion
from ontos.commands.promote import (
    promote_command,
    PromoteOptions,
)

# scaffold - Document scaffolding
from ontos.commands.scaffold import (
    scaffold_command,
    ScaffoldOptions,
    find_untagged_files,
)

# stub - Document scaffolding
from ontos.commands.stub import (
    stub_command,
    StubOptions,
)

__all__ = [
    # Native orchestration (Phase 2)
    "GenerateMapOptions",
    "generate_context_map",
    "EndSessionOptions",
    "create_session_log",
    "suggest_session_impacts",
    "validate_session_concepts",
    # Phase 3: Init
    "InitOptions",
    "init_command",
    "ONTOS_HOOK_MARKER",
    # Phase 4: New commands
    "DoctorOptions",
    "DoctorResult",
    "CheckResult",
    "doctor_command",
    "format_doctor_output",
    "HookOptions",
    "hook_command",
    "ExportOptions",
    "export_command",
    # Wrappers (Phase 2, full impl Phase 4)
    "verify_command",
    "VerifyOptions",
    "find_stale_documents_list",
    "query_command",
    "QueryOptions",
    "scan_docs_for_query",
    "migrate_command",
    "MigrateOptions",
    "consolidate_command",
    "ConsolidateOptions",
    "promote_command",
    "PromoteOptions",
    "scaffold_command",
    "ScaffoldOptions",
    "find_untagged_files",
    "stub_command",
    "StubOptions",
]

