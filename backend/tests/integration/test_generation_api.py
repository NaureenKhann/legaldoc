"""
Integration tests for generation and validation API routes.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_matters_list_api() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/matters")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
