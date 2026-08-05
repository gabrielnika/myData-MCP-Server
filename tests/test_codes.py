from mydata_mcp import codes


def test_invoice_type_label():
    assert codes.invoice_type_label("1.1") == "Sales Invoice (Τιμολόγιο Πώλησης)"
    assert codes.invoice_type_label("11.1") == "Retail Sales Receipt (Απόδειξη Λιανικής Πώλησης)"


def test_invoice_type_label_unknown_returns_none():
    assert codes.invoice_type_label("99.99") is None
    assert codes.invoice_type_label(None) is None


def test_vat_rate():
    assert codes.vat_rate(1) == "24%"
    assert codes.vat_rate("2") == "13%"
    assert codes.vat_rate(7) == "0%"


def test_vat_rate_unknown_returns_none():
    assert codes.vat_rate(99) is None
    assert codes.vat_rate(None) is None


def test_classification_category_label():
    label = codes.classification_category_label("category1_1")
    assert label is not None
    assert "sale of goods" in label.lower()


def test_classification_type_label():
    label = codes.classification_type_label("E3_561_001")
    assert label is not None
    assert "wholesale" in label.lower()
    assert codes.classification_type_label("E3_UNKNOWN_CODE") is None


def test_payment_method_label():
    assert codes.payment_method_label(3) == "Cash (Μετρητά)"
    assert codes.payment_method_label("42") is None
