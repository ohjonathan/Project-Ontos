"""
IO module - File, git, and serialization operations.

Phase 2 creates this layer to isolate I/O operations from core logic.
Core modules should not import from this package directly.
"""

from ontos.io.yaml import parse_yaml, dump_yaml
from ontos.io.git import (
    get_current_branch,
    get_commits_since_push,
    get_changed_files_since_push,
    get_file_mtime,
    is_git_repo,
    get_git_root,
    get_session_git_log,
    get_git_config,
)
from ontos.io.files import (
    find_project_root,
    scan_documents,
    read_document,
    load_document,
    write_text_file,
)
from ontos.io.toml import (
    load_config,
    load_config_if_exists,
    write_config,
    merge_configs,
)
# Phase 3: Config I/O
from ontos.io.config import (
    CONFIG_FILENAME,
    find_config,
    load_project_config,
    save_project_config,
    config_exists,
)

__all__ = [
    # yaml
    "parse_yaml",
    "dump_yaml",
    # git
    "get_current_branch",
    "get_commits_since_push",
    "get_changed_files_since_push",
    "get_file_mtime",
    "is_git_repo",
    "get_git_root",
    "get_session_git_log",
    "get_git_config",
    # files
    "find_project_root",
    "scan_documents",
    "read_document",
    "load_document",
    "write_text_file",
    # toml
    "load_config",
    "load_config_if_exists",
    "write_config",
    "merge_configs",
    # config (Phase 3)
    "CONFIG_FILENAME",
    "find_config",
    "load_project_config",
    "save_project_config",
    "config_exists",
]

