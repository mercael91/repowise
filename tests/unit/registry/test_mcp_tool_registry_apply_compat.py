"""Regression tests for ``MCPToolRegistry.apply`` server compatibility.

The registry registers tools with ``structured_output=False`` so payloads
cross the wire once. Older FastMCP releases do not accept that keyword, so
``apply`` must probe the server's ``tool()`` signature and fall back to a
plain ``mcp.tool()`` call instead of raising ``TypeError``.
"""

from __future__ import annotations

from typing import Any

from repowise.core.registry.mcp_tool_registry import MCPToolRegistry


class _RecordingServer:
    """Minimal FastMCP stand-in that records how tools were registered."""

    def __init__(self, *, accept_structured_output: bool) -> None:
        self.accept_structured_output = accept_structured_output
        self.calls: list[dict[str, Any]] = []

    def tool(self, **kwargs: Any):
        if kwargs and not self.accept_structured_output:
            raise TypeError("tool() got an unexpected keyword argument 'structured_output'")
        self.calls.append(kwargs)

        def _decorator(fn):
            return fn

        return _decorator


def _make_registry() -> MCPToolRegistry:
    registry = MCPToolRegistry()

    @registry.register()
    async def sample_tool(arg: str) -> dict:
        return {"arg": arg}

    return registry


def test_apply_passes_structured_output_false_when_supported():
    registry = _make_registry()
    server = _RecordingServer(accept_structured_output=True)

    registry.apply(server)

    assert server.calls == [{"structured_output": False}]


def test_apply_falls_back_when_structured_output_unsupported():
    registry = _make_registry()
    server = _RecordingServer(accept_structured_output=False)

    registry.apply(server)

    assert server.calls == [{}]


def test_apply_is_idempotent_per_server():
    registry = _make_registry()
    server = _RecordingServer(accept_structured_output=True)

    registry.apply(server)
    registry.apply(server)

    assert len(server.calls) == 1


def test_apply_supports_multiple_servers():
    registry = _make_registry()
    first = _RecordingServer(accept_structured_output=True)
    second = _RecordingServer(accept_structured_output=False)

    registry.apply(first)
    registry.apply(second)

    assert first.calls == [{"structured_output": False}]
    assert second.calls == [{}]
