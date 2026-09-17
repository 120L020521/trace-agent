import asyncio

import pytest

pytest.importorskip("pydantic_settings")
from app.api import main


def test_health_reports_runtime_dependencies(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(main.settings, "amap_api_key", "test-amap-key")
    monkeypatch.setattr(main.shutil, "which", lambda command: "uvx.exe" if command == "uvx" else None)

    result = asyncio.run(main.health())

    assert result["process_healthy"] is True
    assert result["agent_ready"] is True
    assert result["status"] == "ready"
    assert set(result["checks"]) == {"llm", "amap", "mcp_runtime"}


def test_health_is_degraded_without_runtime_dependencies(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(main.settings, "openai_api_key", "")
    monkeypatch.setattr(main.settings, "amap_api_key", "")
    monkeypatch.setattr(main.shutil, "which", lambda command: None)

    result = asyncio.run(main.health())

    assert result["process_healthy"] is True
    assert result["agent_ready"] is False
    assert result["status"] == "degraded"
