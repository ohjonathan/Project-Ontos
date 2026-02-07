"""Regression tests for legacy config compatibility and proposals API exports."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_python(code: str, extra_pythonpath: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run python snippet with controlled PYTHONPATH."""
    pythonpath_parts = [str(PROJECT_ROOT)]
    if extra_pythonpath is not None:
        pythonpath_parts.insert(0, str(extra_pythonpath))

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def test_resolve_config_reads_legacy_ontos_config_from_pythonpath(tmp_path):
    """Legacy ontos_config.py on PYTHONPATH should override defaults."""
    (tmp_path / "ontos_config.py").write_text("LOGS_DIR = 'custom_logs'\n", encoding="utf-8")

    result = _run_python(
        "from ontos.core.paths import resolve_config; print(resolve_config('LOGS_DIR', None))",
        extra_pythonpath=tmp_path,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "custom_logs"


def test_resolve_config_returns_default_without_legacy_config():
    """Without legacy config modules, resolve_config should return provided default."""
    result = _run_python(
        "from ontos.core.paths import resolve_config; print(resolve_config('LOGS_DIR', 'fallback'))"
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "fallback"


def test_resolve_config_emits_legacy_warning_once(tmp_path):
    """Legacy deprecation warning should only be emitted once per process."""
    (tmp_path / "ontos_config.py").write_text("LOGS_DIR = 'custom_logs'\n", encoding="utf-8")

    result = _run_python(
        "\n".join(
            [
                "import warnings",
                "from ontos.core.paths import resolve_config",
                "with warnings.catch_warnings(record=True) as captured:",
                "    warnings.simplefilter('always', FutureWarning)",
                "    resolve_config('LOGS_DIR', None)",
                "    resolve_config('DOCS_DIR', 'docs')",
                "legacy = [w for w in captured if 'Legacy ontos_config.py detected' in str(w.message)]",
                "print(len(legacy))",
            ]
        ),
        extra_pythonpath=tmp_path,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "1"


def test_resolve_config_broken_legacy_config_is_non_fatal(tmp_path):
    """Broken ontos_config.py should warn and fall back to provided default."""
    (tmp_path / "ontos_config.py").write_text(
        "import does_not_exist_anywhere\nLOGS_DIR = 'custom_logs'\n",
        encoding="utf-8",
    )

    result = _run_python(
        "\n".join(
            [
                "import warnings",
                "from ontos.core.paths import resolve_config",
                "with warnings.catch_warnings(record=True) as captured:",
                "    warnings.simplefilter('always', FutureWarning)",
                "    value = resolve_config('LOGS_DIR', 'fallback')",
                "import_warnings = [",
                "    w for w in captured",
                "    if 'Failed to load legacy ontos_config.py' in str(w.message)",
                "]",
                "print(value)",
                "print(len(import_warnings))",
            ]
        ),
        extra_pythonpath=tmp_path,
    )

    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "fallback"
    assert lines[1] == "1"


def test_proposals_exports_ontos_version_constant():
    """ontos.core.proposals should export ONTOS_VERSION."""
    from ontos import __version__
    from ontos.core.proposals import ONTOS_VERSION

    assert ONTOS_VERSION == __version__
