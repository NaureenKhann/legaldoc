"""
Integration tests for document ingestion and matter creation API routes.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        if res.status_code == 404:
            res = await ac.get("/")
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_create_matter_api() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "title": "Integration Test Matter",
            "jurisdiction": "Bombay High Court",
            "case_number": "WP/9999/2026",
            "answering_party": "Respondent No. 2",
        }
        res = await ac.post("/api/v1/matters", json=payload)
        assert res.status_code in (200, 201)
        data = res.json()
        assert "id" in data
        assert data["title"] == "Integration Test Matter"
