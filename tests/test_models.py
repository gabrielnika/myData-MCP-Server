from mydata_mcp.models import Document, Party, Totals, TypeInfo


def test_document_serializes_compactly():
    doc = Document(
        mark="400001000000001",
        type=TypeInfo(code="1.1", label="Sales Invoice (Τιμολόγιο Πώλησης)"),
        issuer=Party(vat="111111111", name="DEMO SUPPLIER SA", country="GR"),
        totals=Totals(net=100.0, vat=24.0, gross=124.0),
        lines_count=1,
    )
    data = doc.model_dump(exclude_none=True)
    assert data["mark"] == "400001000000001"
    assert data["type"]["code"] == "1.1"
    assert data["totals"]["currency"] == "EUR"
    assert "uid" not in data
    assert "lines" not in data
