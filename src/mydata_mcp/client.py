"""Async HTTP client for the AADE myDATA REST API (read-only endpoints).

Credentials come from the environment only and never appear in errors or logs.
"""

import os
from dataclasses import dataclass
from datetime import datetime

import httpx

from .models import BookingRecord, Document
from .normalizer import normalize_bookings, normalize_documents
from .parser import parse_mydata_xml

PRODUCTION_BASE = "https://mydatapi.aade.gr/myDATA/"
SANDBOX_BASE = "https://mydataapidev.aade.gr/"


class MyDataError(Exception):
    """Base error for myDATA client failures."""


class ConfigurationError(MyDataError):
    pass


class AuthenticationError(MyDataError):
    pass


class RateLimitError(MyDataError):
    pass


@dataclass(frozen=True)
class Settings:
    user_id: str
    subscription_key: str
    base_url: str


def load_settings() -> Settings:
    user_id = os.environ.get("MYDATA_USER_ID", "").strip()
    key = os.environ.get("MYDATA_SUBSCRIPTION_KEY", "").strip()
    if not user_id or not key:
        raise ConfigurationError(
            "Missing credentials: set the MYDATA_USER_ID and MYDATA_SUBSCRIPTION_KEY "
            "environment variables (register at https://www.aade.gr/mydata)."
        )
    env = os.environ.get("MYDATA_ENV", "production").strip().lower()
    base_url = SANDBOX_BASE if env == "sandbox" else PRODUCTION_BASE
    return Settings(user_id=user_id, subscription_key=key, base_url=base_url)


def to_api_date(value: str) -> str:
    """Accept YYYY-MM-DD or dd/MM/yyyy; return the API's dd/MM/yyyy."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date {value!r}: use YYYY-MM-DD or dd/MM/yyyy.")


def _raise_on_business_error(parsed: dict) -> None:
    """myDATA sometimes reports errors inside an HTTP 200 body (ResponseDoc)."""
    root = parsed.get("ResponseDoc")
    if not isinstance(root, dict):
        return
    responses = root.get("response")
    responses = responses if isinstance(responses, list) else [responses]
    for resp in responses:
        if not isinstance(resp, dict):
            continue
        status = resp.get("statusCode")
        if status and str(status).lower() != "success":
            errors = (resp.get("errors") or {}).get("error")
            errors = errors if isinstance(errors, list) else ([errors] if errors else [])
            messages = [
                str(e["message"]) for e in errors if isinstance(e, dict) and e.get("message")
            ]
            detail = "; ".join(messages) or str(status)
            raise MyDataError(f"myDATA returned an error: {detail}")


class MyDataClient:
    def __init__(self, settings: Settings | None = None, timeout: float = 30.0):
        self.settings = settings or load_settings()
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "aade-user-id": self.settings.user_id,
            "Ocp-Apim-Subscription-Key": self.settings.subscription_key,
            "Accept": "application/xml",
        }

    async def _get(self, endpoint: str, params: dict) -> str:
        url = f"{self.settings.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            response = await http.get(url, params=params, headers=self._headers())
        if response.status_code in (401, 403):
            raise AuthenticationError(
                "myDATA authentication failed — check MYDATA_USER_ID and MYDATA_SUBSCRIPTION_KEY."
            )
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            hint = f" Retry after {retry_after} seconds." if retry_after else ""
            raise RateLimitError(f"myDATA rate limit exceeded.{hint}")
        if response.status_code >= 400:
            raise MyDataError(
                f"myDATA request to {endpoint} failed with HTTP {response.status_code}."
            )
        return response.text

    async def fetch_documents(
        self,
        endpoint: str,
        *,
        date_from: str,
        date_to: str,
        counterpart_vat: str | None = None,
        invoice_type: str | None = None,
        include_details: bool = False,
        max_results: int = 200,
    ) -> tuple[list[Document], bool]:
        """Fetch from RequestDocs or RequestTransmittedDocs, following continuation tokens.

        Returns (documents, has_more). has_more is True when results were
        truncated at max_results or a continuation token remained unconsumed.
        """
        params: dict = {
            "mark": 0,
            "dateFrom": to_api_date(date_from),
            "dateTo": to_api_date(date_to),
        }
        if counterpart_vat:
            params["counterVatNumber"] = counterpart_vat
        if invoice_type:
            params["invType"] = invoice_type

        documents: list[Document] = []
        continuation: dict | None = None
        while True:
            page_params = dict(params)
            if continuation:
                page_params.update(continuation)
            xml_text = await self._get(endpoint, page_params)
            parsed = parse_mydata_xml(xml_text)
            _raise_on_business_error(parsed)
            batch, continuation = normalize_documents(parsed, include_details=include_details)
            documents.extend(batch)
            if continuation is None or len(documents) >= max_results:
                break
        has_more = continuation is not None or len(documents) > max_results
        return documents[:max_results], has_more

    async def fetch_bookings(
        self,
        endpoint: str,
        *,
        date_from: str,
        date_to: str,
        counterpart_vat: str | None = None,
        max_results: int = 200,
    ) -> tuple[list[BookingRecord], bool]:
        """Fetch from RequestMyIncome or RequestMyExpenses, following continuation tokens."""
        params: dict = {
            "dateFrom": to_api_date(date_from),
            "dateTo": to_api_date(date_to),
        }
        if counterpart_vat:
            params["counterVatNumber"] = counterpart_vat

        records: list[BookingRecord] = []
        continuation: dict | None = None
        while True:
            page_params = dict(params)
            if continuation:
                page_params.update(continuation)
            xml_text = await self._get(endpoint, page_params)
            parsed = parse_mydata_xml(xml_text)
            _raise_on_business_error(parsed)
            batch, continuation = normalize_bookings(parsed)
            records.extend(batch)
            if continuation is None or len(records) >= max_results:
                break
        has_more = continuation is not None or len(records) > max_results
        return records[:max_results], has_more
