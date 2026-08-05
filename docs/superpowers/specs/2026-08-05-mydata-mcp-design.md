# myDATA MCP Server — Design

**Date:** 2026-08-05
**Status:** Approved
**Repo:** standalone public GitHub showcase repo (`mydata-mcp`)

## Purpose

A read-only MCP (Model Context Protocol) server for the Greek AADE myDATA API, letting
LLM clients (Claude Desktop, Claude Code, etc.) query a business's e-books: received and
transmitted documents, and income/expense summaries. Built as a polished open-source
showcase project in Python with FastMCP.

Two goals, in order:
1. **Showcase quality** — clean architecture, typed models, tests, CI, strong README.
2. **Practically useful** — the author (and any Greek business) can point it at real
   myDATA credentials and ask an LLM questions about their invoices.

## Scope

**In scope (read-only myDATA REST endpoints):**
- `RequestDocs` — documents received by the entity (supplier invoices)
- `RequestTransmittedDocs` — documents transmitted by the entity (own issued invoices/receipts)
- `RequestMyIncome` — income bookings per classification
- `RequestMyExpenses` — expense bookings per classification

**Out of scope (explicitly):**
- Any write/send operations (SendInvoices, SendExpensesClassification, cancellations)
- `RequestVatInfo` / `RequestE3Info`
- Local caching, SQLite, analytics/aggregation tools
- The existing SMDeli project — this is a fresh standalone repo; only the battle-tested
  XML-recovery parsing logic is ported (rewritten, not imported).

## Architecture

Language/stack: **Python 3.11+, FastMCP, httpx, xmltodict + lxml (recovery), pydantic v2**.
Packaging with **uv + hatchling**, installable/runnable via `uvx mydata-mcp` (stdio transport).

```
mydata-mcp/
├── pyproject.toml          # uv + hatchling, console script "mydata-mcp"
├── README.md               # English, showcase-quality
├── LICENSE                 # MIT
├── .env.example            # documents env vars, no secrets
├── .gitignore
├── .github/workflows/ci.yml
├── docs/superpowers/specs/ # this design doc
├── src/mydata_mcp/
│   ├── __init__.py
│   ├── server.py           # FastMCP app: 4 tools, 3 resources, 1 prompt; entrypoint
│   ├── client.py           # async httpx client: auth headers, env-based base URL,
│   │                       #   internal pagination loop, HTTP error mapping
│   ├── parser.py           # XML → dict: xmltodict, nested-string handling,
│   │                       #   lxml recover-mode fallback
│   ├── normalizer.py       # raw parsed dict → pydantic models, code decoding
│   ├── codes.py            # static tables: invoice types, VAT categories,
│   │                       #   income/expense classifications, payment methods
│   └── models.py           # pydantic models (Document, Party, Totals, LineItem,
│   │                       #   BookingRecord, PageInfo, ...)
└── tests/
    ├── fixtures/           # anonymized real XML responses
    ├── test_parser.py
    ├── test_normalizer.py
    └── test_server.py      # tool-level tests with respx-mocked HTTP
```

### Component responsibilities

- **server.py** — declares the MCP surface only; no business logic. Each tool validates
  inputs, calls the client, and returns normalized dicts.
- **client.py** — knows myDATA HTTP details: `aade-user-id` / `Ocp-Apim-Subscription-Key`
  headers, production vs sandbox base URL, date param formatting, and the mark/
  nextPartitionKey/nextRowKey continuation loop. Returns raw XML text.
- **parser.py** — turns myDATA XML (including the malformed nested `<string>`-wrapped
  variant) into plain dicts. Strategy: xmltodict → if nested string content, html-unescape
  and re-parse with lxml `recover=True` → fallback to direct xmltodict. (Ported from the
  proven SMDeli implementation.)
- **normalizer.py** — maps parsed dicts to pydantic models and decodes every myDATA code
  via `codes.py`. Output is compact JSON-ready dicts.
- **codes.py** — pure data. Single source of truth for code→label tables, also used to
  render the MCP resources.

## Configuration

Environment variables only (never files in-repo, never logged):

| Variable | Required | Description |
|---|---|---|
| `MYDATA_USER_ID` | yes | AADE user id (`aade-user-id` header) |
| `MYDATA_SUBSCRIPTION_KEY` | yes | Subscription key (`Ocp-Apim-Subscription-Key` header) |
| `MYDATA_ENV` | no (default `production`) | `production` → `https://mydatapi.aade.gr/myDATA/`; `sandbox` → `https://mydataapidev.aade.gr/` |

Missing required vars → server starts but every tool returns a clear configuration error
message (so client setup problems are self-diagnosing inside the LLM conversation).

## MCP surface

### Tools (4)

Common parameters:
- `date_from`, `date_to` (required) — accept ISO `YYYY-MM-DD` or `dd/MM/yyyy`; converted
  internally to the API's `dd/MM/yyyy`.
- `max_results` (default 200) — cap on documents/records returned; the client's internal
  pagination loop stops once reached.
- Responses always include `page_info: {has_more, next_mark}` so the LLM can continue.

| Tool | Endpoint | Extra params | Returns |
|---|---|---|---|
| `get_received_documents` | RequestDocs | `counterpart_vat`, `invoice_type`, `include_details` (bool, default false) | list of received documents |
| `get_transmitted_documents` | RequestTransmittedDocs | `counterpart_vat`, `invoice_type`, `include_details` | list of issued documents |
| `get_income_summary` | RequestMyIncome | `counterpart_vat` | income bookings per classification |
| `get_expense_summary` | RequestMyExpenses | `counterpart_vat` | expense bookings per classification |

### Document output shape (compact by default)

```json
{
  "mark": "400001234567",
  "uid": "ABC123...",
  "issue_date": "2026-07-15",
  "type": {"code": "1.1", "label": "Sales Invoice (Τιμολόγιο Πώλησης)"},
  "issuer": {"vat": "123456789", "name": "SUPPLIER SA", "country": "GR"},
  "counterpart": {"vat": "987654321", "name": "..."},
  "totals": {"net": 100.0, "vat": 24.0, "gross": 124.0, "currency": "EUR"},
  "lines_count": 3
}
```

With `include_details=true`, each document also carries `lines[]` with per-line net/VAT
amounts, decoded VAT category (`{"code": 1, "rate": "24%"}`) and decoded income/expense
classification labels. Income/expense summary records return classification code + E3
label + net/VAT amounts per counterparty entry.

### Resources (3)

Static, rendered from `codes.py` as readable JSON:
- `mydata://codes/invoice-types` — all document types 1.1–17.6, Greek + English labels
- `mydata://codes/vat-categories` — VAT categories with rates (1→24%, 2→13%, …)
- `mydata://codes/classifications` — E3/VAT income & expense classification codes

### Prompt (1)

- `monthly-review(month, year)` — guides the LLM: fetch income and expense summaries for
  the month, fetch received/transmitted documents, and produce a short business review
  (totals, biggest counterparties, anomalies). Demonstrates all three MCP primitives.

## Data flow

tool call → `client` (HTTP GET, pagination loop) → `parser` (XML→dict with recovery) →
`normalizer` (pydantic + code decoding) → compact dict → MCP client.

## Error handling

All failures surface as MCP tool errors with actionable, human-readable text — never
stack traces, never credentials:

- **HTTP 401/403** → "Authentication failed — check MYDATA_USER_ID and MYDATA_SUBSCRIPTION_KEY."
- **HTTP 429** → rate-limit message including Retry-After when present.
- **myDATA business errors** (statusCode/error elements inside a 200 response) → decoded message.
- **XML parse failure** → lxml recovery attempted; if all strategies fail, an error naming
  the failing endpoint and date range.
- **Invalid dates / date_from > date_to** → validation error before any HTTP call.

## Testing

- **pytest + respx** — all HTTP mocked; no network in tests.
- **Fixtures** — anonymized real myDATA XML responses (names/VATs/marks scrambled),
  including one malformed nested-string response to lock in the recovery path.
- **Coverage targets:** parser strategies, normalizer code-decoding, date conversion,
  pagination loop, each tool end-to-end, error mapping (401/429/business error).
- **CI:** GitHub Actions — ruff (lint+format check) and pytest on every push/PR.

## README / showcase requirements (English)

- Badges (CI, PyPI-ready, license), one-paragraph pitch, feature list.
- Mermaid architecture diagram.
- Tools/resources/prompt reference table.
- Quickstart: `uvx mydata-mcp` + Claude Desktop and Claude Code config snippets.
- Example conversation screenshot or transcript.
- Disclaimer: unofficial, read-only, not affiliated with AADE.

## Security

- Read-only by design — no write endpoint is ever called.
- Credentials only via environment variables; `.env.example` documents names with no values.
- Credentials never appear in logs, errors, or tool output.
- The existing `myDataCreds` file in SMDeli stays out of this repo.
