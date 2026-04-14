from datetime import date, timedelta

import pytest

from ontos.core.snapshot import DocumentSnapshot
from ontos.io.snapshot import create_snapshot
from ontos.mcp.bundler import BundleDocument, _lost_in_middle_order, build_context_bundle

from tests.mcp import create_empty_workspace, create_workspace, write_file


def _bundle_doc(doc_id: str, score: float) -> BundleDocument:
    return BundleDocument(id=doc_id, type="atom", status="active", content="", score=score, token_estimate=1)


def _legacy_lost_in_middle_order(docs: list[BundleDocument]) -> list[BundleDocument]:
    ranked = sorted(docs, key=lambda doc: (-doc.score, doc.id))
    front: list[BundleDocument] = []
    back: list[BundleDocument] = []
    for index, doc in enumerate(ranked):
        if index % 2 == 0:
            front.append(doc)
        else:
            back.append(doc)
    return front + list(reversed(back))


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, []),
        (1, ["a"]),
        (2, ["a", "b"]),
        (3, ["a", "c", "b"]),
        (4, ["a", "c", "d", "b"]),
        (5, ["a", "c", "e", "d", "b"]),
        (6, ["a", "c", "e", "f", "d", "b"]),
    ],
)
def test_lost_in_middle_order_matches_fixed_slot_fixture_table(count, expected):
    docs = [_bundle_doc(chr(ord("a") + index), 1.0 - (index * 0.1)) for index in range(count)]

    ordered = _lost_in_middle_order(docs)

    assert [doc.id for doc in ordered] == expected


def test_lost_in_middle_order_matches_legacy_behavior():
    docs = [
        _bundle_doc("alpha", 1.0),
        _bundle_doc("beta", 0.95),
        _bundle_doc("gamma", 0.95),
        _bundle_doc("delta", 0.8),
        _bundle_doc("epsilon", 0.7),
        _bundle_doc("zeta", 0.6),
    ]

    assert _lost_in_middle_order(docs) == _legacy_lost_in_middle_order(docs)


def test_build_context_bundle_scores_kernels_highest(tmp_path):
    root = create_workspace(tmp_path)
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace")
    scores = {item["id"]: item["score"] for item in payload["included_documents"]}

    assert scores["kernel_doc"] == 1.0
    assert all(0.0 <= score <= 1.0 for score in scores.values())


def test_build_context_bundle_greedy_packing_excludes_over_budget_docs(tmp_path):
    root = create_workspace(tmp_path)
    write_file(
        root / "docs/heavy.md",
        f"""
        ---
        id: heavy_doc
        type: reference
        status: active
        depends_on: [kernel_doc]
        ---
        {"heavy " * 2000}
        """,
    )
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace", token_budget=1024)

    included_ids = {item["id"] for item in payload["included_documents"]}
    assert "kernel_doc" in included_ids
    assert "heavy_doc" not in included_ids
    assert payload["excluded_count"] >= 1


def test_build_context_bundle_empty_workspace(tmp_path):
    root = create_empty_workspace(tmp_path)
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "empty")

    assert payload["document_count"] == 0
    assert payload["included_documents"] == []
    assert payload["token_estimate"] == 0


def test_build_context_bundle_budget_smaller_than_kernel_still_includes_kernel(tmp_path):
    root = create_workspace(tmp_path)
    write_file(
        root / "docs/kernel.md",
        f"""
        ---
        id: kernel_doc
        type: kernel
        status: active
        ---
        {"kernel " * 1000}
        """,
    )
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace", token_budget=10)

    ids = [item["id"] for item in payload["included_documents"]]
    assert "kernel_doc" in ids


def test_build_context_bundle_recent_logs_scored_lower(tmp_path):
    root = create_workspace(tmp_path)
    today = date.today().isoformat()
    old = (date.today() - timedelta(days=40)).isoformat()
    write_file(
        root / f"docs/{today}_recent-log.md",
        f"""
        ---
        id: {today}_recent_log
        type: log
        status: active
        date: {today}
        depends_on: [atom_doc]
        ---
        Recent log body.
        """,
    )
    write_file(
        root / f"docs/{old}_old-log.md",
        f"""
        ---
        id: {old}_old_log
        type: log
        status: active
        date: {old}
        depends_on: [atom_doc]
        ---
        Old log body.
        """,
    )
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace")
    score_map = {item["id"]: item["score"] for item in payload["included_documents"]}

    # Under addendum v1.2 §A4 semantics (Dev 4): logs only enter the bundle
    # via the recent-logs pool and only if they fall within log_window_days.
    # The default log_window_days is 30 days, so the 40-day-old log is
    # excluded from the bundle entirely (it no longer reappears in the
    # non-kernel "remaining" bucket at score >= 0.5).
    assert score_map[f"{today}_recent_log"] == 0.3
    assert f"{old}_old_log" not in score_map


def test_build_context_bundle_equal_date_tiebreak_is_deterministic(tmp_path):
    """SF-4: when multiple logs share the same date, the tiebreaker must be
    ascending alphabetical by document ID (per spec v1.1 §4.2 — prompt-cache
    stability). Repeated invocations must produce identical output; the
    previous implementation sorted tuples with ``reverse=True`` which
    flipped the ID tiebreak to *descending* alpha.
    """
    root = create_workspace(tmp_path)
    same_date = date.today().isoformat()
    # Three logs share the same date; write them in non-alphabetical order so
    # that insertion order and alphabetical order disagree.
    for slug in ("zulu", "alpha", "mike"):
        write_file(
            root / f"docs/{same_date}_{slug}.md",
            f"""
            ---
            id: {same_date.replace('-', '_')}_{slug}
            type: log
            status: active
            date: {same_date}
            depends_on: [atom_doc]
            ---
            Same-date log body: {slug}.
            """,
        )

    snapshot = create_snapshot(
        root=root, include_content=True, filters=None, git_commit_provider=None, scope=None
    )

    # Snapshot the order from a few separate builds — all must agree.
    orderings = []
    for _ in range(4):
        payload = build_context_bundle(snapshot, root, "workspace")
        log_ids = [
            item["id"]
            for item in payload["included_documents"]
            if item["type"] == "log" and item["score"] == 0.3 and item["id"].startswith(same_date.replace("-", "_"))
        ]
        orderings.append(tuple(log_ids))

    # Determinism: every invocation produces the same output order.
    assert len(set(orderings)) == 1, orderings

    # And equal-date ties are broken *ascending* alphabetically: alpha < mike < zulu.
    # Note: within-day ascending alpha need not correspond to a specific
    # position in the final reordered bundle, so we verify the sort stability
    # on the recent-logs pool directly via the private helper.
    from ontos.mcp.bundler import _build_priority_order, _to_bundle_doc

    docs_by_id = snapshot.documents
    in_degree = {
        doc_id: len(snapshot.graph.reverse_edges.get(doc_id, []))
        for doc_id in sorted(docs_by_id)
    }
    non_kernel_degrees = [
        in_degree[doc_id]
        for doc_id in in_degree
        if docs_by_id[doc_id].type.value != "kernel"
    ]
    max_non_kernel = max(non_kernel_degrees) if non_kernel_degrees else 0
    scored = [
        _to_bundle_doc(docs_by_id[doc_id], in_degree[doc_id], max_non_kernel)
        for doc_id in sorted(docs_by_id)
    ]
    priority = _build_priority_order(
        scored, docs_by_id, in_degree, root, max_logs=20, log_window_days=30
    )
    same_date_logs = [
        doc.id for doc in priority if doc.type == "log" and doc.id.startswith(same_date.replace("-", "_"))
    ]
    # Ascending-alpha tiebreak: alpha before mike before zulu.
    alpha_id = f"{same_date.replace('-', '_')}_alpha"
    mike_id = f"{same_date.replace('-', '_')}_mike"
    zulu_id = f"{same_date.replace('-', '_')}_zulu"
    assert same_date_logs.index(alpha_id) < same_date_logs.index(mike_id)
    assert same_date_logs.index(mike_id) < same_date_logs.index(zulu_id)


def test_build_context_bundle_stable_across_snapshot_document_orders(tmp_path):
    """SF-B2: bundle output must not depend on ``snapshot.documents`` dict
    insertion order.

    Constructs three snapshots with the SAME document content but
    distinctly-different dict insertion orders (ascending-by-id,
    descending-by-id, and a fixed pathological permutation that puts a
    log first and kernel last). All three must produce identical bundle
    output across ``included_documents``, ``bundle_text``, and
    ``token_estimate``.

    Regression signal — what actually breaks this test:
        - Removing the collective-determinism layer from the bundler
          (i.e. ALL of the ``sorted(...)`` calls in the internal scoring
          / priority / pack / lost-in-middle helpers at once).
        - Introducing a new non-sort mutation of ``docs_by_id`` iteration
          downstream of the existing defensive sorts.

    Known limitation (flagged to orchestrator in PR #92 comment): the
    bundler has multiple redundant defensive sorts (bundler.py lines 55,
    140, 159, 166, 193, 206, 271). Removing any SINGLE one of them does
    NOT break bundle output in isolation because the remaining layers
    preserve determinism. The directive's claim that "deleting ANY
    sorted() call must break the test" is over-strict given the current
    architecture — it would require eliminating most of the defensive
    layers first. This test takes the achievable interpretation: the
    bundler is deterministic under input reordering across three
    distinct permutations. Strictly stronger than the previous
    single-reversal test, but not a per-sort-line regression probe.
    """
    root = create_workspace(tmp_path)
    # Extra docs to broaden the permutation space.
    for slug in ("zulu", "alpha", "mike"):
        write_file(
            root / f"docs/{slug}.md",
            f"""
            ---
            id: {slug}_doc
            type: atom
            status: active
            depends_on: [kernel_doc]
            ---
            Body for {slug}.
            """,
        )

    snapshot = create_snapshot(
        root=root, include_content=True, filters=None,
        git_commit_provider=None, scope=None,
    )

    def _snap_with_document_order(order: list[str]) -> DocumentSnapshot:
        reordered = {doc_id: snapshot.documents[doc_id] for doc_id in order}
        return DocumentSnapshot(
            timestamp=snapshot.timestamp,
            project_root=snapshot.project_root,
            documents=reordered,
            graph=snapshot.graph,
            validation_result=snapshot.validation_result,
            git_commit=snapshot.git_commit,
            ontos_version=snapshot.ontos_version,
            warnings=list(snapshot.warnings),
        )

    doc_ids = list(snapshot.documents.keys())
    asc_order = sorted(doc_ids)
    desc_order = sorted(doc_ids, reverse=True)
    # Pathological: log first, then alternating, kernel last — forces the
    # bundler to reach past natural ordering to produce a canonical bundle.
    log_ids = [d for d in asc_order if d.endswith("_log") or "log" in d]
    kernel_ids = [d for d in asc_order if "kernel" in d]
    other_ids = [d for d in asc_order if d not in log_ids and d not in kernel_ids]
    pathological_order = log_ids + other_ids[::-1] + kernel_ids

    # Sanity: the three orderings must actually differ.
    assert asc_order != desc_order
    assert asc_order != pathological_order
    assert desc_order != pathological_order

    bundle_asc = build_context_bundle(_snap_with_document_order(asc_order), root, "workspace")
    bundle_desc = build_context_bundle(_snap_with_document_order(desc_order), root, "workspace")
    bundle_patho = build_context_bundle(_snap_with_document_order(pathological_order), root, "workspace")

    assert bundle_asc["included_documents"] == bundle_desc["included_documents"]
    assert bundle_asc["included_documents"] == bundle_patho["included_documents"]
    assert bundle_asc["bundle_text"] == bundle_desc["bundle_text"]
    assert bundle_asc["bundle_text"] == bundle_patho["bundle_text"]
    assert bundle_asc["token_estimate"] == bundle_desc["token_estimate"]
    assert bundle_asc["token_estimate"] == bundle_patho["token_estimate"]
