"""myDATA MCP server — read-only access to Greek AADE myDATA e-books."""

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from . import codes
from .client import MyDataClient, MyDataError
from .models import BookingRecord, Document

mcp = FastMCP(
    "myDATA",
    instructions=(
        "Read-only access to the Greek AADE myDATA e-books platform for one business. "
        "Fetch received/transmitted documents and income/expense summaries. All myDATA "
        "codes are decoded to bilingual labels; full code tables are available as "
        "resources under mydata://codes/. Dates accept YYYY-MM-DD or dd/MM/yyyy."
    ),
)


def _doc_response(docs: list[Document], has_more: bool) -> dict:
    marks = [int(d.mark) for d in docs if d.mark and d.mark.isdigit()]
    return {
        "count": len(docs),
        "documents": [d.model_dump(exclude_none=True) for d in docs],
        "page_info": {"has_more": has_more, "next_mark": str(max(marks)) if marks else None},
    }


def _booking_response(records: list[BookingRecord], has_more: bool) -> dict:
    marks = [int(r.max_mark) for r in records if r.max_mark and r.max_mark.isdigit()]
    return {
        "count": len(records),
        "records": [r.model_dump(exclude_none=True) for r in records],
        "page_info": {"has_more": has_more, "next_mark": str(max(marks)) if marks else None},
    }


async def _fetch_documents(endpoint: str, **kwargs) -> dict:
    try:
        client = MyDataClient()
        docs, has_more = await client.fetch_documents(endpoint, **kwargs)
    except (MyDataError, ValueError) as exc:
        raise ToolError(str(exc)) from exc
    return _doc_response(docs, has_more)


async def _fetch_bookings(endpoint: str, **kwargs) -> dict:
    try:
        client = MyDataClient()
        records, has_more = await client.fetch_bookings(endpoint, **kwargs)
    except (MyDataError, ValueError) as exc:
        raise ToolError(str(exc)) from exc
    return _booking_response(records, has_more)


@mcp.tool
async def get_received_documents(
    date_from: str,
    date_to: str,
    counterpart_vat: str | None = None,
    invoice_type: str | None = None,
    include_details: bool = False,
    max_results: int = 200,
) -> dict:
    """Fetch documents RECEIVED by your business (e.g. supplier invoices) from myDATA.

    Args:
        date_from: Start date, YYYY-MM-DD or dd/MM/yyyy.
        date_to: End date, YYYY-MM-DD or dd/MM/yyyy.
        counterpart_vat: Filter by the counterparty's VAT number (ΑΦΜ).
        invoice_type: Filter by myDATA document type code (e.g. "1.1");
            see resource mydata://codes/invoice-types.
        include_details: Include per-line details (VAT categories, classifications).
        max_results: Stop after this many documents; page_info.has_more signals truncation.
    """
    return await _fetch_documents(
        "RequestDocs",
        date_from=date_from,
        date_to=date_to,
        counterpart_vat=counterpart_vat,
        invoice_type=invoice_type,
        include_details=include_details,
        max_results=max_results,
    )


@mcp.tool
async def get_transmitted_documents(
    date_from: str,
    date_to: str,
    counterpart_vat: str | None = None,
    invoice_type: str | None = None,
    include_details: bool = False,
    max_results: int = 200,
) -> dict:
    """Fetch documents ISSUED by your business (sales invoices, receipts) from myDATA.

    Args:
        date_from: Start date, YYYY-MM-DD or dd/MM/yyyy.
        date_to: End date, YYYY-MM-DD or dd/MM/yyyy.
        counterpart_vat: Filter by the customer's VAT number (ΑΦΜ).
        invoice_type: Filter by myDATA document type code (e.g. "11.1");
            see resource mydata://codes/invoice-types.
        include_details: Include per-line details (VAT categories, classifications).
        max_results: Stop after this many documents; page_info.has_more signals truncation.
    """
    return await _fetch_documents(
        "RequestTransmittedDocs",
        date_from=date_from,
        date_to=date_to,
        counterpart_vat=counterpart_vat,
        invoice_type=invoice_type,
        include_details=include_details,
        max_results=max_results,
    )


@mcp.tool
async def get_income_summary(
    date_from: str,
    date_to: str,
    counterpart_vat: str | None = None,
    max_results: int = 200,
) -> dict:
    """Fetch INCOME bookings per classification from myDATA e-books (RequestMyIncome).

    Each record aggregates documents per counterparty/type/classification with
    net, VAT, and gross totals. Classification codes are decoded to labels.

    Args:
        date_from: Start date, YYYY-MM-DD or dd/MM/yyyy.
        date_to: End date, YYYY-MM-DD or dd/MM/yyyy.
        counterpart_vat: Filter by the counterparty's VAT number (ΑΦΜ).
        max_results: Stop after this many records; page_info.has_more signals truncation.
    """
    return await _fetch_bookings(
        "RequestMyIncome",
        date_from=date_from,
        date_to=date_to,
        counterpart_vat=counterpart_vat,
        max_results=max_results,
    )


@mcp.tool
async def get_expense_summary(
    date_from: str,
    date_to: str,
    counterpart_vat: str | None = None,
    max_results: int = 200,
) -> dict:
    """Fetch EXPENSE bookings per classification from myDATA e-books (RequestMyExpenses).

    Each record aggregates documents per counterparty/type/classification with
    net, VAT, and gross totals. Classification codes are decoded to labels.

    Args:
        date_from: Start date, YYYY-MM-DD or dd/MM/yyyy.
        date_to: End date, YYYY-MM-DD or dd/MM/yyyy.
        counterpart_vat: Filter by the counterparty's VAT number (ΑΦΜ).
        max_results: Stop after this many records; page_info.has_more signals truncation.
    """
    return await _fetch_bookings(
        "RequestMyExpenses",
        date_from=date_from,
        date_to=date_to,
        counterpart_vat=counterpart_vat,
        max_results=max_results,
    )


@mcp.resource("mydata://codes/invoice-types")
def invoice_types() -> dict:
    """All myDATA document type codes (1.1-17.6) with English and Greek labels."""
    return codes.INVOICE_TYPES


@mcp.resource("mydata://codes/vat-categories")
def vat_categories() -> dict:
    """myDATA VAT category codes with rates and labels."""
    return {str(code): entry for code, entry in codes.VAT_CATEGORIES.items()}


@mcp.resource("mydata://codes/classifications")
def classifications() -> dict:
    """myDATA income/expense classification categories and common E3 types."""
    return {
        "categories": codes.CLASSIFICATION_CATEGORIES,
        "types": codes.CLASSIFICATION_TYPES,
    }


@mcp.prompt
def monthly_review(month: int, year: int) -> str:
    """Produce a monthly business review from myDATA data."""
    period = f"{month:02d}/{year}"
    first_day = f"{year}-{month:02d}-01"
    return f"""You have read-only myDATA tools for a Greek business.

Prepare a business review for {period}:

1. Call get_income_summary and get_expense_summary from {first_day} to the last
   day of that month.
2. Call get_transmitted_documents and get_received_documents for the same period.
3. Read mydata://codes/classifications if any classification code is unfamiliar.

Report, in this order:
- Total income and expenses (net, VAT, gross) and the resulting gross margin.
- Top 5 counterparties by gross value on each side (suppliers and customers).
- Income and expense breakdown by classification category.
- Anything unusual: credit notes (types 5.1/5.2/11.4), cancelled documents, or
  outliers relative to the rest of the month.

Present amounts in EUR with thousands separators."""


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
