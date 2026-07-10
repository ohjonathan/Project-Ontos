"""Shared error taxonomy for CLI command routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OntosUserError(Exception):
    """User-facing error caused by invalid input or usage."""

    message: str
    code: str = "E_USER_INPUT"
    details: Optional[str] = None

    def __str__(self) -> str:
        return self.message


@dataclass
class OntosInternalError(Exception):
    """Internal command/runtime error with optional machine-readable code."""

    message: str
    code: str = "E_INTERNAL"
    details: Optional[str] = None

    def __str__(self) -> str:
        return self.message
