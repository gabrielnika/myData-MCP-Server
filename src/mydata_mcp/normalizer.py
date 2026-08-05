"""Turn parsed myDATA XML dicts into typed, code-decoded models.

All access is defensive (.get everywhere): the API omits elements freely, and
xmltodict returns a dict instead of a list when an element appears once.
"""

from typing import Any

from . import codes
from .models import (
    BookingRecord,
    Classification,
    Document,
    LineItem,
    Party,
    Totals,
    TypeInfo,
    VatInfo,
)


def _as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _text(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("#text")
    return str(value) if value is not None else None


def _to_float(value: Any) -> float | None:
    try:
        return float(_text(value))
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(_text(value))
    except (TypeError, ValueError):
        return None


def _type_info(code: Any) -> TypeInfo | None:
    code = _text(code)
    if not code:
        return None
    return TypeInfo(code=code, label=codes.invoice_type_label(code))


def _party(raw: Any) -> Party | None:
    if not isinstance(raw, dict):
        return None
    return Party(
        vat=_text(raw.get("vatNumber")),
        name=_text(raw.get("name")),
        country=_text(raw.get("country")),
        branch=_to_int(raw.get("branch")),
    )


def _classification(raw: dict) -> Classification:
    category = _text(raw.get("classificationCategory"))
    ctype = _text(raw.get("classificationType"))
    return Classification(
        category=category,
        category_label=codes.classification_category_label(category),
        type=ctype,
        type_label=codes.classification_type_label(ctype),
        amount=_to_float(raw.get("amount")),
    )


def _line(raw: dict) -> LineItem:
    vat_code = _to_int(raw.get("vatCategory"))
    classifications = [
        _classification(c)
        for key in ("incomeClassification", "expensesClassification")
        for c in _as_list(raw.get(key))
        if isinstance(c, dict)
    ]
    return LineItem(
        line_number=_to_int(raw.get("lineNumber")),
        net_value=_to_float(raw.get("netValue")),
        vat=VatInfo(code=vat_code, rate=codes.vat_rate(vat_code)) if vat_code is not None else None,
        vat_amount=_to_float(raw.get("vatAmount")),
        classifications=classifications,
    )


def _continuation(raw: Any) -> dict | None:
    if not isinstance(raw, dict):
        return None
    partition = _text(raw.get("nextPartitionKey"))
    row = _text(raw.get("nextRowKey"))
    if partition and row:
        return {"nextPartitionKey": partition, "nextRowKey": row}
    return None


def _document(raw: dict, include_details: bool) -> Document:
    header = raw.get("invoiceHeader") or {}
    summary = raw.get("invoiceSummary") or {}
    lines = [line for line in _as_list(raw.get("invoiceDetails")) if isinstance(line, dict)]
    return Document(
        mark=_text(raw.get("mark")),
        uid=_text(raw.get("uid")),
        cancelled_by_mark=_text(raw.get("cancelledByMark")),
        issue_date=_text(header.get("issueDate")),
        series=_text(header.get("series")),
        number=_text(header.get("aa")),
        type=_type_info(header.get("invoiceType")),
        issuer=_party(raw.get("issuer")),
        counterpart=_party(raw.get("counterpart")),
        totals=Totals(
            net=_to_float(summary.get("totalNetValue")),
            vat=_to_float(summary.get("totalVatAmount")),
            gross=_to_float(summary.get("totalGrossValue")),
            currency=_text(header.get("currency")) or "EUR",
        ),
        lines_count=len(lines),
        lines=[_line(line) for line in lines] if include_details else None,
    )


def normalize_documents(
    parsed: dict, *, include_details: bool = False
) -> tuple[list[Document], dict | None]:
    """Return (documents, continuation) from a RequestDocs/RequestTransmittedDocs response.

    continuation is {"nextPartitionKey": ..., "nextRowKey": ...} or None when
    the result set is complete.
    """
    root = parsed.get("RequestedDoc") or {}
    invoices = _as_list((root.get("invoicesDoc") or {}).get("invoice"))
    documents = [_document(inv, include_details) for inv in invoices if isinstance(inv, dict)]
    return documents, _continuation(root.get("continuationToken"))


def normalize_bookings(parsed: dict) -> tuple[list[BookingRecord], dict | None]:
    """Return (records, continuation) from a RequestMyIncome/RequestMyExpenses response.

    The live API emits <bookInfo> elements; the myDATA docs also mention
    booksInfo, so both spellings are accepted.
    """
    root = parsed.get("RequestedBookInfo") or {}
    raw_records = root.get("bookInfo")
    if raw_records is None:
        raw_records = root.get("booksInfo")
    records: list[BookingRecord] = []
    for raw in _as_list(raw_records):
        if not isinstance(raw, dict):
            continue
        has_classification = raw.get("classificationCategory") or raw.get("classificationType")
        records.append(
            BookingRecord(
                counterpart_vat=_text(raw.get("counterVatNumber")),
                issue_date=_text(raw.get("issueDate")),
                type=_type_info(raw.get("invType")),
                net_value=_to_float(raw.get("netValue")),
                vat_amount=_to_float(raw.get("vatAmount")),
                gross_value=_to_float(raw.get("grossValue")),
                count=_to_int(raw.get("count")),
                min_mark=_text(raw.get("minMark")),
                max_mark=_text(raw.get("maxMark")),
                classification=_classification(raw) if has_classification else None,
            )
        )
    return records, _continuation(root.get("continuationToken"))
