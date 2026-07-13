from pathlib import Path

import pytest

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


def test_duplicate_destinations_are_rejected_before_journal_write(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("before", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate rename destination"):
        RenameTransaction.prepare(tmp_path, [doc, doc])

    assert not (tmp_path / JOURNAL_RELATIVE_PATH).exists()
