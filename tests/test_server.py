import json
from pathlib import Path

import pytest
import respx
from fastmcp import Client
from httpx import Response

from mydata_mcp.client import PRODUCTION_BASE
from mydata_mcp.server import mcp

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _payload(result):
    """Tolerate fastmcp version differences in structured-result access."""
    if getattr(result, "data", None) is not None:
        return result.data
    return json.loads(result.content[0].text)


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv("MYDATA_USER_ID", "testuser")
    monkeypatch.setenv("MYDATA_SUBSCRIPTION_KEY", "testkey")
    monkeypatch.delenv("MYDATA_ENV", raising=False)


@respx.mock
async def test_get_received_documents(creds):
    respx.get(f"{PRODUCTION_BASE}RequestDocs").mock(
        return_value=Response(200, text=_fixture("received_docs_page2.xml"))
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_received_documents",
            {"date_from": "2026-07-01", "date_to": "2026-07-31"},
        )
    data = _payload(result)
    assert data["count"] == 1
    doc = data["documents"][0]
    assert doc["mark"] == "400001000000003"
    assert doc["type"]["label"] == "Service Invoice (Τιμολόγιο Παροχής Υπηρεσιών)"
    assert data["page_info"] == {"has_more": False, "next_mark": "400001000000003"}


@respx.mock
async def test_get_transmitted_documents_uses_correct_endpoint(creds):
    route = respx.get(f"{PRODUCTION_BASE}RequestTransmittedDocs").mock(
        return_value=Response(200, text=_fixture("received_docs_page2.xml"))
    )
    async with Client(mcp) as client:
        await client.call_tool(
            "get_transmitted_documents",
            {"date_from": "2026-07-01", "date_to": "2026-07-31", "counterpart_vat": "222222222"},
        )
    assert route.call_count == 1
    assert "counterVatNumber=222222222" in str(route.calls[0].request.url)


@respx.mock
async def test_get_income_summary(creds):
    respx.get(f"{PRODUCTION_BASE}RequestMyIncome").mock(
        return_value=Response(200, text=_fixture("bookings_income.xml"))
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_income_summary", {"date_from": "2026-07-01", "date_to": "2026-07-31"}
        )
    data = _payload(result)
    assert data["count"] == 2
    assert data["records"][0]["classification"]["type"] == "E3_561_001"


@respx.mock
async def test_get_expense_summary_uses_correct_endpoint(creds):
    route = respx.get(f"{PRODUCTION_BASE}RequestMyExpenses").mock(
        return_value=Response(200, text=_fixture("bookings_income.xml"))
    )
    async with Client(mcp) as client:
        await client.call_tool(
            "get_expense_summary", {"date_from": "2026-07-01", "date_to": "2026-07-31"}
        )
    assert route.call_count == 1


async def test_missing_credentials_error_is_actionable(monkeypatch):
    monkeypatch.delenv("MYDATA_USER_ID", raising=False)
    monkeypatch.delenv("MYDATA_SUBSCRIPTION_KEY", raising=False)
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="MYDATA_USER_ID"):
            await client.call_tool(
                "get_received_documents",
                {"date_from": "2026-07-01", "date_to": "2026-07-31"},
            )


async def test_invalid_date_error_is_actionable(creds):
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="YYYY-MM-DD"):
            await client.call_tool(
                "get_received_documents",
                {"date_from": "bogus", "date_to": "2026-07-31"},
            )


async def test_code_table_resources():
    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "mydata://codes/invoice-types" in uris
        assert "mydata://codes/vat-categories" in uris
        assert "mydata://codes/classifications" in uris
        content = await client.read_resource("mydata://codes/invoice-types")
        body = json.loads(content[0].text)
        assert body["1.1"]["en"] == "Sales Invoice"


async def test_monthly_review_prompt():
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        assert any(p.name == "monthly_review" for p in prompts)
        rendered = await client.get_prompt("monthly_review", {"month": 7, "year": 2026})
        text = rendered.messages[0].content.text
        assert "07/2026" in text
        assert "get_income_summary" in text
