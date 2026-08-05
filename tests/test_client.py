from pathlib import Path

import pytest
import respx
from httpx import Response

from mydata_mcp.client import (
    PRODUCTION_BASE,
    SANDBOX_BASE,
    AuthenticationError,
    ConfigurationError,
    MyDataClient,
    MyDataError,
    RateLimitError,
    Settings,
    load_settings,
    to_api_date,
)

FIXTURES = Path(__file__).parent / "fixtures"

TEST_SETTINGS = Settings(user_id="testuser", subscription_key="testkey", base_url=PRODUCTION_BASE)


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_to_api_date_accepts_iso_and_greek():
    assert to_api_date("2026-07-01") == "01/07/2026"
    assert to_api_date("01/07/2026") == "01/07/2026"


def test_to_api_date_rejects_garbage():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        to_api_date("July 1st")


def test_load_settings_requires_credentials(monkeypatch):
    monkeypatch.delenv("MYDATA_USER_ID", raising=False)
    monkeypatch.delenv("MYDATA_SUBSCRIPTION_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="MYDATA_USER_ID"):
        load_settings()


def test_load_settings_sandbox(monkeypatch):
    monkeypatch.setenv("MYDATA_USER_ID", "u")
    monkeypatch.setenv("MYDATA_SUBSCRIPTION_KEY", "k")
    monkeypatch.setenv("MYDATA_ENV", "sandbox")
    assert load_settings().base_url == SANDBOX_BASE


@respx.mock
async def test_authentication_error_is_actionable():
    respx.get(f"{PRODUCTION_BASE}RequestDocs").mock(return_value=Response(401))
    client = MyDataClient(settings=TEST_SETTINGS)
    with pytest.raises(AuthenticationError, match="MYDATA_SUBSCRIPTION_KEY"):
        await client.fetch_documents("RequestDocs", date_from="2026-07-01", date_to="2026-07-31")


@respx.mock
async def test_rate_limit_error_includes_retry_after():
    respx.get(f"{PRODUCTION_BASE}RequestDocs").mock(
        return_value=Response(429, headers={"Retry-After": "60"})
    )
    client = MyDataClient(settings=TEST_SETTINGS)
    with pytest.raises(RateLimitError, match="60"):
        await client.fetch_documents("RequestDocs", date_from="2026-07-01", date_to="2026-07-31")


BUSINESS_ERROR_XML = """<?xml version="1.0" encoding="utf-8"?>
<ResponseDoc xmlns="http://www.aade.gr/myDATA/responseDoc/v1.0">
  <response>
    <statusCode>ValidationError</statusCode>
    <errors>
      <error>
        <message>Invalid Greek VAT number</message>
        <code>204</code>
      </error>
    </errors>
  </response>
</ResponseDoc>"""


@respx.mock
async def test_business_error_inside_200_response_is_decoded():
    respx.get(f"{PRODUCTION_BASE}RequestDocs").mock(
        return_value=Response(200, text=BUSINESS_ERROR_XML)
    )
    client = MyDataClient(settings=TEST_SETTINGS)
    with pytest.raises(MyDataError, match="Invalid Greek VAT number"):
        await client.fetch_documents("RequestDocs", date_from="2026-07-01", date_to="2026-07-31")


@respx.mock
async def test_pagination_follows_continuation_token():
    route = respx.get(f"{PRODUCTION_BASE}RequestDocs")
    route.side_effect = [
        Response(200, text=_fixture("received_docs_page1.xml")),
        Response(200, text=_fixture("received_docs_page2.xml")),
    ]
    client = MyDataClient(settings=TEST_SETTINGS)
    docs, has_more = await client.fetch_documents(
        "RequestDocs", date_from="2026-07-01", date_to="2026-07-31"
    )
    assert len(docs) == 3
    assert has_more is False
    assert route.call_count == 2
    second_url = str(route.calls[1].request.url)
    assert "nextPartitionKey" in second_url
    assert "nextRowKey" in second_url


@respx.mock
async def test_pagination_stops_at_max_results():
    route = respx.get(f"{PRODUCTION_BASE}RequestDocs")
    route.side_effect = [Response(200, text=_fixture("received_docs_page1.xml"))]
    client = MyDataClient(settings=TEST_SETTINGS)
    docs, has_more = await client.fetch_documents(
        "RequestDocs", date_from="2026-07-01", date_to="2026-07-31", max_results=2
    )
    assert len(docs) == 2
    assert has_more is True  # continuation token was left unconsumed
    assert route.call_count == 1


@respx.mock
async def test_fetch_bookings():
    respx.get(f"{PRODUCTION_BASE}RequestMyIncome").mock(
        return_value=Response(200, text=_fixture("bookings_income.xml"))
    )
    client = MyDataClient(settings=TEST_SETTINGS)
    records, has_more = await client.fetch_bookings(
        "RequestMyIncome", date_from="2026-07-01", date_to="2026-07-31"
    )
    assert len(records) == 2
    assert has_more is False
    assert records[0].classification.type == "E3_561_001"
