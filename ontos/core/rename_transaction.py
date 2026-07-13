"""Durable recovery journal for multi-file document ID renames.

The journal is intentionally independent of git.  A rename records the exact
pre-write bytes for every destination before :class:`SessionContext` starts
replacing files.  If the process exits mid-commit, the next CLI or MCP rename
restores those bytes while holding the workspace lock.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from uuid import uuid4


JOURNAL_RELATIVE_PATH = Path(".ontos") / "transactions" / "rename.json"
_STAGING_NONCE_LENGTH = 24


def _journal_path(root: Path) -> Path:
    root = root.resolve()
    path = root / JOURNAL_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or root not in path.parent.resolve().parents:
        raise RuntimeError("Rename transaction directory escapes the workspace")
    return path


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_bytes(path: Path, content: bytes) -> None:
    temp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(temp, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        _fsync_directory(path.parent)
    except BaseException:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        raise


@dataclass
class RenameTransaction:
    root: Path
    journal: Path
    staging_token: str
    destinations: Tuple[Path, ...]

    @classmethod
    def prepare(cls, root: Path, paths: Iterable[Path]) -> "RenameTransaction":
        root = root.resolve()
        journal = _journal_path(root)
        if journal.exists():
            raise RuntimeError(
                "An incomplete rename transaction already exists; recover it first"
            )

        entries = []
        destinations = []
        seen = set()
        for candidate in sorted((Path(path).resolve() for path in paths), key=str):
            if candidate in seen:
                raise ValueError(f"Duplicate rename destination: {candidate}")
            seen.add(candidate)
            try:
                relative = candidate.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"Rename destination escapes workspace: {candidate}") from exc
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError(f"Rename destination is not a regular file: {candidate}")
            destinations.append(candidate)
            entries.append(
                {
                    "path": relative.as_posix(),
                    "content_b64": base64.b64encode(candidate.read_bytes()).decode("ascii"),
                }
            )

        staging_token = uuid4().hex
        payload = {
            "schema_version": 2,
            "operation": "rename",
            "state": "prepared",
            "staging_token": staging_token,
            "entries": entries,
        }
        _atomic_bytes(
            journal,
            (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"),
        )
        return cls(
            root=root,
            journal=journal,
            staging_token=staging_token,
            destinations=tuple(destinations),
        )

    def complete(self) -> None:
        _cleanup_staging_artifacts(
            self.destinations,
            staging_token=self.staging_token,
        )
        self.journal.unlink(missing_ok=True)
        _fsync_directory(self.journal.parent)

    def rollback(self) -> List[Path]:
        return recover_rename_transaction(self.root)


def recover_rename_transaction(root: Path) -> List[Path]:
    """Restore and clear an interrupted rename journal, if present."""

    root = root.resolve()
    journal = _journal_path(root)
    if not journal.exists():
        return []
    if journal.is_symlink() or not journal.is_file():
        raise RuntimeError("Rename transaction journal is not a regular file")

    try:
        payload = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Rename transaction journal is unreadable: {exc}") from exc
    schema_version = payload.get("schema_version")
    if (
        schema_version not in {1, 2}
        or payload.get("operation") != "rename"
        or payload.get("state") != "prepared"
        or not isinstance(payload.get("entries"), list)
    ):
        raise RuntimeError("Rename transaction journal has an unsupported shape")
    staging_token = payload.get("staging_token") if schema_version == 2 else None
    if schema_version == 2 and not _valid_staging_token(staging_token):
        raise RuntimeError("Rename transaction journal has an invalid staging token")

    restored: List[Path] = []
    for entry in payload["entries"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise RuntimeError("Rename transaction journal contains an invalid entry")
        destination = (root / entry["path"]).resolve()
        try:
            destination.relative_to(root)
        except ValueError as exc:
            raise RuntimeError("Rename transaction entry escapes the workspace") from exc
        if destination.is_symlink():
            raise RuntimeError(f"Refusing to restore through symlink: {destination}")
        try:
            content = base64.b64decode(entry["content_b64"], validate=True)
        except Exception as exc:
            raise RuntimeError("Rename transaction backup is invalid") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        _atomic_bytes(destination, content)
        restored.append(destination)

    if staging_token is not None:
        _cleanup_staging_artifacts(restored, staging_token=staging_token)

    journal.unlink()
    _fsync_directory(journal.parent)
    return restored


def _valid_staging_token(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 32
        and all(char in "0123456789abcdef" for char in value)
    )


def _cleanup_staging_artifacts(
    destinations: Sequence[Path],
    *,
    staging_token: str,
) -> None:
    """Remove token-bound SessionContext artifacts for touched paths only."""

    if not _valid_staging_token(staging_token):
        raise RuntimeError("Invalid transaction staging token")

    changed_directories: set[Path] = set()
    for destination in destinations:
        parent = destination.parent
        prefix = f".{destination.name}.{staging_token}."
        try:
            candidates = list(parent.iterdir())
        except FileNotFoundError:
            continue
        for candidate in candidates:
            name = candidate.name
            if not name.startswith(prefix):
                continue
            if name.endswith(".tmp"):
                nonce = name[len(prefix) : -len(".tmp")]
            elif name.endswith(".bak"):
                nonce = name[len(prefix) : -len(".bak")]
            else:
                continue
            if len(nonce) != _STAGING_NONCE_LENGTH or any(
                char not in "0123456789abcdef" for char in nonce
            ):
                continue
            if candidate.is_symlink() or not candidate.is_file():
                raise RuntimeError(
                    f"Refusing to remove non-regular rename staging artifact: {candidate}"
                )
            candidate.unlink()
            changed_directories.add(parent)

    for directory in sorted(changed_directories, key=str):
        _fsync_directory(directory)
