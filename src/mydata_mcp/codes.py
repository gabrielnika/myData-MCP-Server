"""Static myDATA code tables — single source of truth for code → label decoding.

Tables are curated from the AADE myDATA specification. They cover the codes a
Greek business commonly encounters; unknown codes decode to None and are passed
through unchanged by the normalizer.
"""

from typing import Any

INVOICE_TYPES: dict[str, dict[str, str]] = {
    "1.1": {"en": "Sales Invoice", "el": "Τιμολόγιο Πώλησης"},
    "1.2": {"en": "Sales Invoice / Intra-community Supplies", "el": "Τιμολόγιο Πώλησης / Ενδοκοινοτικές Παραδόσεις"},
    "1.3": {"en": "Sales Invoice / Third Country Supplies", "el": "Τιμολόγιο Πώλησης / Παραδόσεις Τρίτων Χωρών"},
    "1.4": {"en": "Sales Invoice / Sale on Behalf of Third Parties", "el": "Τιμολόγιο Πώλησης / Πώληση για Λογαριασμό Τρίτων"},
    "1.5": {"en": "Sales Invoice / Third-party Sales Clearance", "el": "Τιμολόγιο Πώλησης / Εκκαθάριση Πωλήσεων Τρίτων"},
    "1.6": {"en": "Sales Invoice / Supplementary Document", "el": "Τιμολόγιο Πώλησης / Συμπληρωματικό Παραστατικό"},
    "2.1": {"en": "Service Invoice", "el": "Τιμολόγιο Παροχής Υπηρεσιών"},
    "2.2": {"en": "Service Invoice / Intra-community Services", "el": "Τιμολόγιο Παροχής / Ενδοκοινοτική Παροχή Υπηρεσιών"},
    "2.3": {"en": "Service Invoice / Third Country Services", "el": "Τιμολόγιο Παροχής / Παροχή Υπηρεσιών σε λήπτη Τρίτης Χώρας"},
    "2.4": {"en": "Service Invoice / Supplementary Document", "el": "Τιμολόγιο Παροχής / Συμπληρωματικό Παραστατικό"},
    "3.1": {"en": "Proof of Expenditure (non-liable issuer)", "el": "Τίτλος Κτήσης (μη υπόχρεος Εκδότης)"},
    "3.2": {"en": "Proof of Expenditure (issuance refusal)", "el": "Τίτλος Κτήσης (άρνηση έκδοσης από υπόχρεο Εκδότη)"},
    "5.1": {"en": "Credit Invoice / Associated", "el": "Πιστωτικό Τιμολόγιο / Συσχετιζόμενο"},
    "5.2": {"en": "Credit Invoice / Non-Associated", "el": "Πιστωτικό Τιμολόγιο / Μη Συσχετιζόμενο"},
    "6.1": {"en": "Self-Delivery Record", "el": "Στοιχείο Αυτοπαράδοσης"},
    "6.2": {"en": "Self-Supply Record", "el": "Στοιχείο Ιδιοχρησιμοποίησης"},
    "7.1": {"en": "Contract - Income", "el": "Συμβόλαιο - Έσοδο"},
    "8.1": {"en": "Rents - Income", "el": "Ενοίκια - Έσοδο"},
    "8.2": {"en": "Accommodation Tax Receipt", "el": "Απόδειξη Είσπραξης Φόρου Διαμονής"},
    "9.3": {"en": "Dispatch Note", "el": "Δελτίο Αποστολής"},
    "11.1": {"en": "Retail Sales Receipt", "el": "Απόδειξη Λιανικής Πώλησης"},
    "11.2": {"en": "Retail Service Receipt", "el": "Απόδειξη Παροχής Υπηρεσιών"},
    "11.3": {"en": "Simplified Invoice", "el": "Απλοποιημένο Τιμολόγιο"},
    "11.4": {"en": "Retail Credit Note", "el": "Πιστωτικό Στοιχείο Λιανικής"},
    "11.5": {"en": "Retail Sales Receipt on Behalf of Third Parties", "el": "Απόδειξη Λιανικής Πώλησης για Λογαριασμό Τρίτων"},
    "13.1": {"en": "Expenses - Retail Purchases (domestic/foreign)", "el": "Έξοδα - Αγορές Λιανικών Συναλλαγών ημεδαπής/αλλοδαπής"},
    "13.2": {"en": "Retail Services Received (domestic/foreign)", "el": "Παροχή Λιανικών Συναλλαγών ημεδαπής/αλλοδαπής"},
    "13.3": {"en": "Shared Utilities", "el": "Κοινόχρηστα"},
    "13.4": {"en": "Subscriptions", "el": "Συνδρομές"},
    "13.30": {"en": "Self-Declared Entity Documents (retail)", "el": "Παραστατικά Οντότητας ως Αναγράφονται από την ίδια (Δυναμικό)"},
    "13.31": {"en": "Retail Credit Note (domestic/foreign)", "el": "Πιστωτικό Στοιχείο Λιανικής ημεδαπής/αλλοδαπής"},
    "14.1": {"en": "Invoice / Intra-community Acquisitions", "el": "Τιμολόγιο / Ενδοκοινοτικές Αποκτήσεις"},
    "14.2": {"en": "Invoice / Third Country Acquisitions", "el": "Τιμολόγιο / Αποκτήσεις Τρίτων Χωρών"},
    "14.3": {"en": "Invoice / Intra-community Services Received", "el": "Τιμολόγιο / Ενδοκοινοτική Λήψη Υπηρεσιών"},
    "14.4": {"en": "Invoice / Third Country Services Received", "el": "Τιμολόγιο / Λήψη Υπηρεσιών Τρίτων Χωρών"},
    "14.5": {"en": "EFKA and Insurance Organizations", "el": "ΕΦΚΑ και λοιποί Ασφαλιστικοί Οργανισμοί"},
    "14.30": {"en": "Self-Declared Entity Documents", "el": "Παραστατικά Οντότητας ως Αναγράφονται από την ίδια (Δυναμικό)"},
    "14.31": {"en": "Credit Note (domestic/foreign)", "el": "Πιστωτικό ημεδαπής/αλλοδαπής"},
    "15.1": {"en": "Contract - Expense", "el": "Συμβόλαιο - Έξοδο"},
    "16.1": {"en": "Rent - Expense", "el": "Ενοίκιο - Έξοδο"},
    "17.1": {"en": "Payroll", "el": "Μισθοδοσία"},
    "17.2": {"en": "Depreciation", "el": "Αποσβέσεις"},
    "17.3": {"en": "Other Income Adjustment Entries - Accounting Base", "el": "Λοιπές Εγγραφές Τακτοποίησης Εσόδων - Λογιστική Βάση"},
    "17.4": {"en": "Other Income Adjustment Entries - Tax Base", "el": "Λοιπές Εγγραφές Τακτοποίησης Εσόδων - Φορολογική Βάση"},
    "17.5": {"en": "Other Expense Adjustment Entries - Accounting Base", "el": "Λοιπές Εγγραφές Τακτοποίησης Εξόδων - Λογιστική Βάση"},
    "17.6": {"en": "Other Expense Adjustment Entries - Tax Base", "el": "Λοιπές Εγγραφές Τακτοποίησης Εξόδων - Φορολογική Βάση"},
}

VAT_CATEGORIES: dict[int, dict[str, Any]] = {
    1: {"rate": "24%", "en": "Standard rate 24%", "el": "ΦΠΑ συντελεστής 24%"},
    2: {"rate": "13%", "en": "Reduced rate 13%", "el": "ΦΠΑ συντελεστής 13%"},
    3: {"rate": "6%", "en": "Super-reduced rate 6%", "el": "ΦΠΑ συντελεστής 6%"},
    4: {"rate": "17%", "en": "Island standard rate 17%", "el": "ΦΠΑ συντελεστής 17% (νησιά)"},
    5: {"rate": "9%", "en": "Island reduced rate 9%", "el": "ΦΠΑ συντελεστής 9% (νησιά)"},
    6: {"rate": "4%", "en": "Island super-reduced rate 4%", "el": "ΦΠΑ συντελεστής 4% (νησιά)"},
    7: {"rate": "0%", "en": "Without VAT (0%)", "el": "Άνευ ΦΠΑ (0%)"},
    8: {"rate": None, "en": "Records without VAT", "el": "Εγγραφές χωρίς ΦΠΑ"},
    9: {"rate": "3%", "en": "Reduced rate 3%", "el": "ΦΠΑ συντελεστής 3%"},
    10: {"rate": "4%", "en": "Rate 4%", "el": "ΦΠΑ συντελεστής 4%"},
}

CLASSIFICATION_CATEGORIES: dict[str, dict[str, str]] = {
    "category1_1": {"en": "Revenue from sale of goods", "el": "Έσοδα από Πώληση Εμπορευμάτων"},
    "category1_2": {"en": "Revenue from sale of products", "el": "Έσοδα από Πώληση Προϊόντων"},
    "category1_3": {"en": "Revenue from provision of services", "el": "Έσοδα από Παροχή Υπηρεσιών"},
    "category1_4": {"en": "Revenue from sale of fixed assets", "el": "Έσοδα από Πώληση Παγίων"},
    "category1_5": {"en": "Other income and gains", "el": "Λοιπά Έσοδα/Κέρδη"},
    "category1_6": {"en": "Self-deliveries / self-use", "el": "Αυτοπαραδόσεις / Ιδιοχρησιμοποιήσεις"},
    "category1_7": {"en": "Revenue on behalf of third parties", "el": "Έσοδα για λογαριασμό τρίτων"},
    "category1_8": {"en": "Prior-year revenue", "el": "Έσοδα προηγούμενων χρήσεων"},
    "category1_9": {"en": "Deferred revenue", "el": "Έσοδα επομένων χρήσεων"},
    "category1_10": {"en": "Other revenue adjustment entries", "el": "Λοιπές Εγγραφές Τακτοποίησης Εσόδων"},
    "category1_95": {"en": "Other informational revenue data", "el": "Λοιπά Πληροφοριακά Στοιχεία Εσόδων"},
    "category2_1": {"en": "Purchases of goods", "el": "Αγορές Εμπορευμάτων"},
    "category2_2": {"en": "Purchases of raw materials", "el": "Αγορές Α'-Β' Υλών"},
    "category2_3": {"en": "Services received", "el": "Λήψη Υπηρεσιών"},
    "category2_4": {"en": "General expenses with VAT deduction right", "el": "Γενικά Έξοδα με δικαίωμα έκπτωσης ΦΠΑ"},
    "category2_5": {"en": "General expenses without VAT deduction right", "el": "Γενικά Έξοδα χωρίς δικαίωμα έκπτωσης ΦΠΑ"},
    "category2_6": {"en": "Personnel fees and benefits", "el": "Αμοιβές και Παροχές Προσωπικού"},
    "category2_7": {"en": "Purchases of fixed assets", "el": "Αγορές Παγίων"},
    "category2_8": {"en": "Depreciation of fixed assets", "el": "Αποσβέσεις Παγίων"},
    "category2_9": {"en": "Expenses on behalf of third parties", "el": "Έξοδα για λογαριασμό τρίτων"},
    "category2_10": {"en": "Prior-year expenses", "el": "Έξοδα προηγούμενων χρήσεων"},
    "category2_11": {"en": "Deferred expenses", "el": "Έξοδα επομένων χρήσεων"},
    "category2_12": {"en": "Other expense adjustment entries", "el": "Λοιπές Εγγραφές Τακτοποίησης Εξόδων"},
    "category2_95": {"en": "Other informational expense data", "el": "Λοιπά Πληροφοριακά Στοιχεία Εξόδων"},
    "category3": {"en": "Movement of goods", "el": "Διακίνηση"},
}

CLASSIFICATION_TYPES: dict[str, dict[str, str]] = {
    # Income (E3 revenue codes)
    "E3_561_001": {"en": "Wholesale sales of goods and services to businesses", "el": "Πωλήσεις αγαθών και υπηρεσιών Χονδρικές - Επιτηδευματιών"},
    "E3_561_002": {"en": "Wholesale sales under article 39a", "el": "Πωλήσεις αγαθών και υπηρεσιών Χονδρικές βάσει άρθρου 39α"},
    "E3_561_003": {"en": "Retail sales to private customers", "el": "Πωλήσεις αγαθών και υπηρεσιών Λιανικές - Ιδιωτική Πελατεία"},
    "E3_561_004": {"en": "Retail sales under article 39a", "el": "Πωλήσεις αγαθών και υπηρεσιών Λιανικές βάσει άρθρου 39α"},
    "E3_561_005": {"en": "Intra-EU foreign sales", "el": "Πωλήσεις αγαθών και υπηρεσιών Εξωτερικού Ενδοκοινοτικές"},
    "E3_561_006": {"en": "Third-country foreign sales", "el": "Πωλήσεις αγαθών και υπηρεσιών Εξωτερικού Τρίτες Χώρες"},
    "E3_561_007": {"en": "Other sales of goods and services", "el": "Πωλήσεις αγαθών και υπηρεσιών Λοιπά"},
    "E3_562": {"en": "Other ordinary income", "el": "Λοιπά συνήθη έσοδα"},
    "E3_563": {"en": "Credit interest and related income", "el": "Πιστωτικοί τόκοι και συναφή έσοδα"},
    "E3_564": {"en": "Credit exchange differences", "el": "Πιστωτικές συναλλαγματικές διαφορές"},
    "E3_565": {"en": "Income from participations", "el": "Έσοδα συμμετοχών"},
    "E3_566": {"en": "Gains from disposal of non-current assets", "el": "Κέρδη από διάθεση μη κυκλοφορούντων περιουσιακών στοιχείων"},
    "E3_567": {"en": "Gains from reversal of provisions and impairments", "el": "Κέρδη από αναστροφή προβλέψεων και απομειώσεων"},
    "E3_568": {"en": "Fair value measurement gains", "el": "Κέρδη από επιμέτρηση στην εύλογη αξία"},
    "E3_570": {"en": "Extraordinary income and gains", "el": "Ασυνήθη έσοδα και κέρδη"},
    "E3_595": {"en": "Self-production expenses", "el": "Έξοδα σε ιδιοπαραγωγή"},
    "E3_596": {"en": "Subsidies and grants", "el": "Επιδοτήσεις - Επιχορηγήσεις"},
    "E3_597": {"en": "Investment subsidies and grants", "el": "Επιδοτήσεις - Επιχορηγήσεις για επενδυτικούς σκοπούς"},
    # Expenses (E3 expense codes)
    "E3_102_001": {"en": "Purchases of goods - wholesale", "el": "Αγορές εμπορευμάτων χρήσης (καθαρό ποσό) - Χονδρικές"},
    "E3_102_002": {"en": "Purchases of goods - retail", "el": "Αγορές εμπορευμάτων χρήσης (καθαρό ποσό) - Λιανικές"},
    "E3_102_003": {"en": "Purchases of goods - intra-EU", "el": "Αγορές εμπορευμάτων χρήσης - Εξωτερικού Ενδοκοινοτικές"},
    "E3_102_004": {"en": "Purchases of goods - third countries", "el": "Αγορές εμπορευμάτων χρήσης - Εξωτερικού Τρίτες Χώρες"},
    "E3_102_005": {"en": "Purchases of goods - other", "el": "Αγορές εμπορευμάτων χρήσης - Λοιπά"},
    "E3_202_001": {"en": "Purchases of raw materials - wholesale", "el": "Αγορές πρώτων και βοηθητικών υλών - Χονδρικές"},
    "E3_202_002": {"en": "Purchases of raw materials - retail", "el": "Αγορές πρώτων και βοηθητικών υλών - Λιανικές"},
    "E3_202_003": {"en": "Purchases of raw materials - intra-EU", "el": "Αγορές πρώτων και βοηθητικών υλών - Εξωτερικού Ενδοκοινοτικές"},
    "E3_202_004": {"en": "Purchases of raw materials - third countries", "el": "Αγορές πρώτων και βοηθητικών υλών - Εξωτερικού Τρίτες Χώρες"},
    "E3_202_005": {"en": "Purchases of raw materials - other", "el": "Αγορές πρώτων και βοηθητικών υλών - Λοιπά"},
    "E3_581_001": {"en": "Employee benefits - gross wages", "el": "Παροχές σε εργαζόμενους - Μικτές αποδοχές"},
    "E3_581_002": {"en": "Employee benefits - employer contributions", "el": "Παροχές σε εργαζόμενους - Εργοδοτικές εισφορές"},
    "E3_581_003": {"en": "Employee benefits - other benefits", "el": "Παροχές σε εργαζόμενους - Λοιπές παροχές"},
    "E3_582": {"en": "Asset measurement losses", "el": "Ζημιές επιμέτρησης περιουσιακών στοιχείων"},
    "E3_583": {"en": "Debit exchange differences", "el": "Χρεωστικές συναλλαγματικές διαφορές"},
    "E3_584": {"en": "Losses from disposal of non-current assets", "el": "Ζημιές από διάθεση μη κυκλοφορούντων περιουσιακών στοιχείων"},
    "E3_586": {"en": "Debit interest and related expenses", "el": "Χρεωστικοί τόκοι και συναφή έξοδα"},
    "E3_587": {"en": "Depreciation", "el": "Αποσβέσεις"},
    "E3_588": {"en": "Extraordinary expenses, losses and fines", "el": "Ασυνήθη έξοδα, ζημιές και πρόστιμα"},
    "E3_589": {"en": "Provisions", "el": "Προβλέψεις"},
}

PAYMENT_METHODS: dict[int, dict[str, str]] = {
    1: {"en": "Domestic business bank account", "el": "Επαγγελματικός Λογαριασμός Πληρωμών Ημεδαπής"},
    2: {"en": "Foreign business bank account", "el": "Επαγγελματικός Λογαριασμός Πληρωμών Αλλοδαπής"},
    3: {"en": "Cash", "el": "Μετρητά"},
    4: {"en": "Check", "el": "Επιταγή"},
    5: {"en": "On credit", "el": "Επί πιστώσει"},
    6: {"en": "Web banking", "el": "Web banking"},
    7: {"en": "POS / e-POS", "el": "POS / e-POS"},
}


def _label(entry: dict[str, Any] | None) -> str | None:
    if not entry:
        return None
    en, el = entry.get("en"), entry.get("el")
    if en and el and en != el:
        return f"{en} ({el})"
    return en or el


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def invoice_type_label(code: Any) -> str | None:
    if code is None:
        return None
    return _label(INVOICE_TYPES.get(str(code)))


def vat_rate(code: Any) -> str | None:
    entry = VAT_CATEGORIES.get(_safe_int(code))
    return entry.get("rate") if entry else None


def classification_category_label(code: Any) -> str | None:
    if code is None:
        return None
    return _label(CLASSIFICATION_CATEGORIES.get(str(code)))


def classification_type_label(code: Any) -> str | None:
    if code is None:
        return None
    return _label(CLASSIFICATION_TYPES.get(str(code)))


def payment_method_label(code: Any) -> str | None:
    return _label(PAYMENT_METHODS.get(_safe_int(code)))
