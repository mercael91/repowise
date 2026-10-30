"""Regression tests for ``module:`` target expansion in get_health."""

from __future__ import annotations

from dataclasses import dataclass

from repowise.server.mcp_server.tool_health.targets import (
    _expand_module_targets,
    _unresolved_targets,
)


@dataclass
class _Metric:
    module: str
    file_path: str


METRICS = [
    _Metric(module="src", file_path="src/main.py"),
    _Metric(module="src/auth", file_path="src/auth/login.py"),
    _Metric(module="src/auth/deep", file_path="src/auth/deep/token.py"),
    _Metric(module="docs", file_path="docs/index.md"),
]


def test_nested_module_target_matches() -> None:
    paths, matched = _expand_module_targets(METRICS, ["src/auth"], [])
    assert matched == {"src/auth"}
    assert paths == ["src/auth/deep/token.py", "src/auth/login.py"]


def test_overlapping_targets_all_matched() -> None:
    paths, matched = _expand_module_targets(METRICS, ["src", "src/auth"], [])
    assert matched == {"src", "src/auth"}
    assert paths == [
        "src/auth/deep/token.py",
        "src/auth/login.py",
        "src/main.py",
    ]


def test_overlapping_targets_not_reported_unresolved() -> None:
    paths, matched = _expand_module_targets(METRICS, ["src", "src/auth"], [])
    unresolved = _unresolved_targets(
        file_targets=[],
        module_targets=["src", "src/auth"],
        matched_modules=matched,
        resolved_paths=set(paths),
        excluded_paths=set(),
        unscored_paths=set(),
        repo_root=None,
    )
    assert unresolved == []


def test_missing_module_still_reported() -> None:
    _, matched = _expand_module_targets(METRICS, ["src", "nope"], [])
    unresolved = _unresolved_targets(
        file_targets=[],
        module_targets=["src", "nope"],
        matched_modules=matched,
        resolved_paths=set(),
        excluded_paths=set(),
        unscored_paths=set(),
        repo_root=None,
    )
    assert unresolved == [{"target": "module:nope", "reason": "no_such_module"}]


def test_no_module_targets_keeps_order() -> None:
    paths, matched = _expand_module_targets(METRICS, [], ["b.py", "a.py"])
    assert paths == ["b.py", "a.py"]
    assert matched == set()
