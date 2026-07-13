import json
import os
from pathlib import Path

import pytest

from ontos.core.context import SessionContext
from ontos.core.rename_transaction import (
    JOURNAL_RELATIVE_PATH,
    RenameTransaction,
    recover_rename_transaction,
)


def test_interrupted_rename_restores_all_original_bytes(tmp_path: Path) -> None:
    first = tmp_path / "docs" / "first.md"
    second = tmp_path / "docs" / "second.md"
    first.parent.mkdir()
    first.write_bytes(b"first-before\r\n")
    second.write_bytes(b"second-before\n")

    RenameTransaction.prepare(tmp_path, [first, second])
    first.write_bytes(b"first-after\n")
    second.write_bytes(b"second-after\n")

    restored = recover_rename_transaction(tmp_path)

    assert restored == [first, second]
    assert first.read_bytes() == b"first-before\r\n"
    assert second.read_bytes() == b"second-before\n"
    assert not (tmp_path / JOURNAL_RELATIVE_PATH).exists()


def test_successful_transaction_removes_journal_without_rollback(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "doc.md"
    doc.parent.mkdir()
    doc.write_text("before", encoding="utf-8")
    transaction = RenameTransaction.prepare(tmp_path, [doc])
    doc.write_text("after", encoding="utf-8")

    transaction.complete()

    assert recover_rename_transaction(tmp_path) == []
    assert doc.read_text(encoding="utf-8") == "after"


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_successful_transaction_skips_non_regular_staging_artifacts(
    tmp_path: Path,
) -> None:
    doc = tmp_path / "docs" / "doc.md"
    doc.parent.mkdir()
    doc.write_text("before", encoding="utf-8")
    transaction = RenameTransaction.prepare(tmp_path, [doc])
    symlink = doc.parent / (
        f".{doc.name}.{transaction.staging_token}.{'1' * 24}.tmp"
    )
    directory = doc.parent / (
        f".{doc.name}.{transaction.staging_token}.{'2' * 24}.bak"
    )
    try:
        symlink.symlink_to(doc)
    except OSError as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")
    directory.mkdir()
    doc.write_text("after", encoding="utf-8")

    transaction.complete()

    assert not transaction.journal.exists()
    assert symlink.is_symlink()
    assert directory.is_dir()
    assert doc.read_text(encoding="utf-8") == "after"


def test_duplicate_destinations_are_rejected_before_journal_write(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("before", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate rename destination"):
        RenameTransaction.prepare(tmp_path, [doc, doc])

    assert not (tmp_path / JOURNAL_RELATIVE_PATH).exists()


def test_recovery_accepts_schema_v1_journal(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "doc.md"
    doc.parent.mkdir()
    doc.write_bytes(b"before\n")
    transaction = RenameTransaction.prepare(tmp_path, [doc])
    payload = json.loads(transaction.journal.read_text(encoding="utf-8"))
    payload["schema_version"] = 1
    payload.pop("staging_token")
    transaction.journal.write_text(json.dumps(payload), encoding="utf-8")
    doc.write_bytes(b"after\n")

    restored = recover_rename_transaction(tmp_path)

    assert restored == [doc]
    assert doc.read_bytes() == b"before\n"
    assert not transaction.journal.exists()


def test_recovery_removes_only_token_bound_session_staging_artifacts(
    tmp_path: Path,
) -> None:
    doc = tmp_path / "docs" / "doc.md"
    doc.parent.mkdir()
    doc.write_bytes(b"before\n")
    transaction = RenameTransaction.prepare(tmp_path, [doc])
    ctx = SessionContext(
        repo_root=tmp_path,
        config={},
        staging_token=transaction.staging_token,
    )

    anchor = ctx._open_parent_anchor(doc, create=False)
    try:
        temp_name, _ = ctx._stage_text(anchor, doc.name, "after\n")
        backup_name, _ = ctx._reserve_backup(anchor, doc.name)
    finally:
        ctx._close_anchor(anchor)

    unrelated = doc.parent / f".{doc.name}.{'0' * 32}.{'1' * 24}.tmp"
    unrelated.write_text("keep", encoding="utf-8")
    doc.write_bytes(b"after\n")

    restored = recover_rename_transaction(tmp_path)

    assert restored == [doc]
    assert doc.read_bytes() == b"before\n"
    assert not (doc.parent / temp_name).exists()
    assert not (doc.parent / backup_name).exists()
    assert unrelated.read_text(encoding="utf-8") == "keep"
    assert not (tmp_path / JOURNAL_RELATIVE_PATH).exists()


def test_recovery_tolerates_staging_artifact_unlink_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc = tmp_path / "docs" / "doc.md"
    doc.parent.mkdir()
    doc.write_bytes(b"before\n")
    transaction = RenameTransaction.prepare(tmp_path, [doc])
    artifact = doc.parent / (
        f".{doc.name}.{transaction.staging_token}.{'3' * 24}.tmp"
    )
    artifact.write_text("staged", encoding="utf-8")
    doc.write_bytes(b"after\n")

    original_unlink = Path.unlink
    raced = False

    def unlink_with_race(path: Path, *args: object, **kwargs: object) -> None:
        nonlocal raced
        if path == artifact and not raced:
            raced = True
            original_unlink(path)
            raise FileNotFoundError(path)
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", unlink_with_race)

    restored = recover_rename_transaction(tmp_path)

    assert raced is True
    assert restored == [doc]
    assert doc.read_bytes() == b"before\n"
    assert not transaction.journal.exists()

    next_transaction = RenameTransaction.prepare(tmp_path, [doc])
    next_transaction.complete()
    assert not next_transaction.journal.exists()
