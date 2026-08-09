import json

import pytest
import respx
from httpx import Response

from mydata_mcp import audit

BQ_URL = (
    "https://bigquery.googleapis.com/bigquery/v2/projects/proj/datasets/ds/tables/events/insertAll"
)


@pytest.fixture(autouse=True)
def reset_token_cache():
    audit._token_cache.update({"token": None, "expires": 0.0})


async def test_noop_without_audit_table(monkeypatch):
    monkeypatch.delenv("AUDIT_TABLE", raising=False)
    # No respx mock active: any HTTP attempt would raise.
    await audit.record("RequestDocs", "success", 12, result_count=3)


@respx.mock
async def test_inserts_row_with_expected_shape(monkeypatch):
    monkeypatch.setenv("AUDIT_TABLE", "proj.ds.events")
    respx.get(audit.METADATA_TOKEN_URL).mock(
        return_value=Response(200, json={"access_token": "tok", "expires_in": 3600})
    )
    route = respx.post(BQ_URL).mock(return_value=Response(200, json={}))

    await audit.record("RequestDocs", "success", 42, result_count=7)

    assert route.call_count == 1
    request = route.calls[0].request
    assert request.headers["authorization"] == "Bearer tok"
    row = json.loads(request.content)["rows"][0]["json"]
    assert row["tool"] == "RequestDocs"
    assert row["status"] == "success"
    assert row["duration_ms"] == 42
    assert row["result_count"] == 7
    assert "error_type" not in row  # None fields are dropped
    assert "ts" in row


@respx.mock
async def test_caches_metadata_token(monkeypatch):
    monkeypatch.setenv("AUDIT_TABLE", "proj.ds.events")
    token_route = respx.get(audit.METADATA_TOKEN_URL).mock(
        return_value=Response(200, json={"access_token": "tok", "expires_in": 3600})
    )
    respx.post(BQ_URL).mock(return_value=Response(200, json={}))

    await audit.record("RequestDocs", "success", 1)
    await audit.record("RequestDocs", "error", 2, error_type="ValueError")

    assert token_route.call_count == 1


@respx.mock
async def test_swallows_bigquery_failure(monkeypatch):
    monkeypatch.setenv("AUDIT_TABLE", "proj.ds.events")
    respx.get(audit.METADATA_TOKEN_URL).mock(
        return_value=Response(200, json={"access_token": "tok", "expires_in": 3600})
    )
    respx.post(BQ_URL).mock(return_value=Response(500, text="boom"))

    await audit.record("RequestDocs", "success", 1)  # must not raise


async def test_server_emits_audit_events(monkeypatch):
    events = []

    async def fake_record(tool, status, duration_ms, result_count=None, error_type=None):
        events.append({"tool": tool, "status": status, "error_type": error_type})

    from mydata_mcp import server

    monkeypatch.setattr(server.audit, "record", fake_record)
    monkeypatch.setenv("MYDATA_USER_ID", "u")
    monkeypatch.setenv("MYDATA_SUBSCRIPTION_KEY", "k")

    with pytest.raises(Exception):
        await server._fetch_documents("RequestDocs", date_from="bogus", date_to="2026-07-31")

    assert events == [{"tool": "RequestDocs", "status": "error", "error_type": "ValueError"}]
