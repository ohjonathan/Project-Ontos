"""Shared error taxonomy for CLI command routing."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from typing import Optional


class _FieldImmutableException(Exception):
    """Preserve frozen public fields while allowing exception runtime state.

    ``contextlib`` assigns ``__traceback__`` while propagating an exception
    through a generator context manager on supported Python versions. A
    frozen dataclass rejects that assignment and replaces the real error with
    ``FrozenInstanceError``. Keep the v4.7.0 field-immutability/hash contract
    while permitting only the metadata attributes owned by ``BaseException``.
    """

    _ontos_fields_locked = False
    _runtime_attributes = frozenset(
        {
            "__traceback__",
            "__cause__",
            "__context__",
            "__suppress_context__",
            "__notes__",
        }
    )

    def _lock_public_fields(self) -> None:
        object.__setattr__(self, "_ontos_fields_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if self._ontos_fields_locked and name not in self._runtime_attributes:
            raise FrozenInstanceError(f"cannot assign to field {name!r}")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if self._ontos_fields_locked and name not in self._runtime_attributes:
            raise FrozenInstanceError(f"cannot delete field {name!r}")
        object.__delattr__(self, name)


@dataclass(unsafe_hash=True)
class OntosUserError(_FieldImmutableException):
    """User-facing error caused by invalid input or usage."""

    message: str
    code: str = "E_USER_INPUT"
    details: Optional[str] = None

    def __post_init__(self) -> None:
        self._lock_public_fields()

    def __str__(self) -> str:
        return self.message


@dataclass(unsafe_hash=True)
class OntosInternalError(_FieldImmutableException):
    """Internal command/runtime error with optional machine-readable code."""

    message: str
    code: str = "E_INTERNAL"
    details: Optional[str] = None

    def __post_init__(self) -> None:
        self._lock_public_fields()

    def __str__(self) -> str:
        return self.message
