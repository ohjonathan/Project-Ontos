"""Shared content-hash utilities.

Lives in ``ontos.core`` so it can be consumed by both command-layer modules
and the portfolio / bridge modules without creating a layering inversion
(see m-10 in v4.1 Track A/D verdict).
"""

from __future__ import annotations

import hashlib


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content, returned as ``sha256:<16-hex-prefix>``.

    The 16-character truncation matches the historical format emitted by
    ``ontos.commands.export_data`` and consumed by the MCP portfolio index,
    the MCP tools response bodies, and downstream tests.
    """
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}"
