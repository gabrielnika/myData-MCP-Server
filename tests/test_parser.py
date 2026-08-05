from pathlib import Path

from mydata_mcp.parser import parse_mydata_xml

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parses_wellformed_response():
    parsed = parse_mydata_xml(_load("received_docs_page1.xml"))
    root = parsed["RequestedDoc"]
    invoices = root["invoicesDoc"]["invoice"]
    assert len(invoices) == 2
    assert invoices[0]["mark"] == "400001000000001"
    assert root["continuationToken"]["nextPartitionKey"] == "1!8!partition2"


def test_strips_namespace_prefixes():
    parsed = parse_mydata_xml(_load("received_docs_page1.xml"))
    line = parsed["RequestedDoc"]["invoicesDoc"]["invoice"][0]["invoiceDetails"]
    classification = line["incomeClassification"]
    # icls: prefixes must be stripped so the normalizer sees plain keys
    assert classification["classificationType"] == "E3_561_001"
    assert classification["classificationCategory"] == "category1_1"


def test_recovers_nested_malformed_response():
    parsed = parse_mydata_xml(_load("received_docs_nested_malformed.xml"))
    invoice = parsed["RequestedDoc"]["invoicesDoc"]["invoice"]
    assert invoice["mark"] == "400001000000009"
    assert invoice["issuer"]["vatNumber"] == "555555555"
    # lxml recovery may mangle the text around the bare "&" but structure survives
    assert "SMITH" in (invoice["issuer"]["name"] or "")


def test_single_invoice_is_dict_not_list():
    parsed = parse_mydata_xml(_load("received_docs_page2.xml"))
    invoice = parsed["RequestedDoc"]["invoicesDoc"]["invoice"]
    assert isinstance(invoice, dict)  # xmltodict quirk the normalizer must handle
