"""Fire-and-forget usage audit to BigQuery via the streaming-insert REST API.

Enabled only when AUDIT_TABLE (``project.dataset.table``) is set — locally it
is absent and every call is a no-op. Tokens come from the Cloud Run metadata
server, so no extra dependencies or stored keys are needed. Only metadata is
recorded (tool, timing, status) — never myDATA payload contents. Failures are
swallowed: audit must never break or noticeably slow a tool call.
"""

import os
import time
import uuid
from datetime import UTC, datetime

import httpx

METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
)

_token_cache: dict = {"token": None, "expires": 0.0}


def _table() -> tuple[str, str, str] | None:
    parts = os.environ.get("AUDIT_TABLE", "").strip().split(".")
    return (parts[0], parts[1], parts[2]) if len(parts) == 3 and all(parts) else None


async def _access_token(client: httpx.AsyncClient) -> str:
    now = time.monotonic()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]
    resp = await client.get(METADATA_TOKEN_URL, headers={"Metadata-Flavor": "Google"})
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires"] = now + data.get("expires_in", 300) - 60
    return _token_cache["token"]


async def record(
    tool: str,
    status: str,
    duration_ms: int,
    result_count: int | None = None,
    error_type: str | None = None,
) -> None:
    target = _table()
    if target is None:
        return
    project, dataset, table = target
    url = (
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}"
        f"/datasets/{dataset}/tables/{table}/insertAll"
    )
    row = {
        "ts": datetime.now(UTC).isoformat(),
        "tool": tool,
        "status": status,
        "duration_ms": duration_ms,
        "result_count": result_count,
        "error_type": error_type,
    }
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            token = await _access_token(client)
            await client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "rows": [
                        {
                            "insertId": str(uuid.uuid4()),
                            "json": {k: v for k, v in row.items() if v is not None},
                        }
                    ]
                },
            )
    except Exception:
        # Audit is best-effort by design; tool calls must never fail because of it.
        pass
