"""Typed output models — the compact JSON shapes returned to MCP clients."""

from pydantic import BaseModel


class TypeInfo(BaseModel):
    code: str
    label: str | None = None


class Party(BaseModel):
    vat: str | None = None
    name: str | None = None
    country: str | None = None
    branch: int | None = None


class VatInfo(BaseModel):
    code: int | None = None
    rate: str | None = None


class Classification(BaseModel):
    category: str | None = None
    category_label: str | None = None
    type: str | None = None
    type_label: str | None = None
    amount: float | None = None


class LineItem(BaseModel):
    line_number: int | None = None
    net_value: float | None = None
    vat: VatInfo | None = None
    vat_amount: float | None = None
    classifications: list[Classification] = []


class Totals(BaseModel):
    net: float | None = None
    vat: float | None = None
    gross: float | None = None
    currency: str = "EUR"


class Document(BaseModel):
    mark: str | None = None
    uid: str | None = None
    cancelled_by_mark: str | None = None
    issue_date: str | None = None
    series: str | None = None
    number: str | None = None
    type: TypeInfo | None = None
    issuer: Party | None = None
    counterpart: Party | None = None
    totals: Totals | None = None
    lines_count: int = 0
    lines: list[LineItem] | None = None


class BookingRecord(BaseModel):
    counterpart_vat: str | None = None
    issue_date: str | None = None
    type: TypeInfo | None = None
    net_value: float | None = None
    vat_amount: float | None = None
    gross_value: float | None = None
    count: int | None = None
    min_mark: str | None = None
    max_mark: str | None = None
    classification: Classification | None = None
