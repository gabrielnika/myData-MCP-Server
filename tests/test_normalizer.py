from pathlib import Path

from mydata_mcp.normalizer import normalize_bookings, normalize_documents
from mydata_mcp.parser import parse_mydata_xml

FIXTURES = Path(__file__).parent / "fixtures"


def _parsed(name: str) -> dict:
    return parse_mydata_xml((FIXTURES / name).read_text(encoding="utf-8"))


def test_normalizes_documents_compact():
    docs, continuation = normalize_documents(_parsed("received_docs_page1.xml"))
    assert len(docs) == 2
    first = docs[0]
    assert first.mark == "400001000000001"
    assert first.issue_date == "2026-07-10"
    assert first.type.code == "1.1"
    assert first.type.label == "Sales Invoice (Τιμολόγιο Πώλησης)"
    assert first.issuer.vat == "111111111"
    assert first.counterpart.vat == "222222222"
    assert first.totals.net == 100.0
    assert first.totals.gross == 124.0
    assert first.lines_count == 1
    assert first.lines is None  # compact by default
    assert continuation == {"nextPartitionKey": "1!8!partition2", "nextRowKey": "1!12!row2"}


def test_normalizes_documents_with_details():
    docs, _ = normalize_documents(_parsed("received_docs_page1.xml"), include_details=True)
    line = docs[0].lines[0]
    assert line.net_value == 100.0
    assert line.vat.code == 1
    assert line.vat.rate == "24%"
    cls = line.classifications[0]
    assert cls.type == "E3_561_001"
    assert "wholesale" in cls.type_label.lower()
    assert cls.category == "category1_1"
    assert cls.amount == 100.0


def test_retail_receipt_has_no_counterpart():
    docs, _ = normalize_documents(_parsed("received_docs_page1.xml"))
    receipt = docs[1]
    assert receipt.counterpart is None
    assert receipt.type.code == "11.1"


def test_single_invoice_response():
    docs, continuation = normalize_documents(_parsed("received_docs_page2.xml"))
    assert len(docs) == 1
    assert docs[0].mark == "400001000000003"
    assert continuation is None


def test_normalizes_income_bookings():
    records, continuation = normalize_bookings(_parsed("bookings_income.xml"))
    assert len(records) == 2
    first = records[0]
    assert first.counterpart_vat == "555555555"
    assert first.net_value == 1500.0
    assert first.gross_value == 1860.0
    assert first.count == 3
    assert first.max_mark == "400001000000103"
    assert first.type.code == "1.1"
    assert first.classification.type == "E3_561_001"
    assert "wholesale" in first.classification.type_label.lower()
    assert "sale of goods" in first.classification.category_label.lower()
    assert continuation is None


def test_bookings_from_empty_response():
    records, continuation = normalize_bookings({"RequestedBookInfo": None})
    assert records == []
    assert continuation is None
