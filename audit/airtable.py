"""Direct Airtable REST reads, for when a key exists.

Airtable reaches this repo two ways, and the difference matters:

- **Through the MCP**, which is the *model's* tool. Python cannot call it. A
  skill fetches records and hands them to `main.py copy-sync` on stdin.
- **Through this module**, which needs `AIRTABLE_API_KEY` in the environment.
  No key is set today, so this path is dormant.

Both land in the same place. `outbound/copy_sync.py` validates and writes a
snapshot; `outbound/anchors.py` reads it. The point of two paths is that adding
the key later turns the manual sync automatic with no other change — and until
then, nothing silently half-works: `available()` is False, and the caller falls
through to the snapshot and then to the CSVs.

Reads are unrestricted. Writes are deliberately narrow: `update_records` exists
so a finished batch can report usage back to Copy Assets, which is the only way
the weights ever stop being guesses. Nothing here creates or deletes a table,
and nothing writes a Lead — that stays in the skill layer where a human sees it.
"""

from __future__ import annotations

import os

import requests

API_ROOT = "https://api.airtable.com/v0"
TIMEOUT = 20

# The live base. Recorded here rather than passed in, because a typo'd base ID
# that silently reads the wrong table is worse than a missing key.
BASE_ID = "appejF07kunksqt4D"
COPY_ASSETS_TABLE = "Copy Assets"


class AirtableError(RuntimeError):
    pass


def available() -> bool:
    """True when a direct read is possible. False is normal, not an error."""
    return bool(os.environ.get("AIRTABLE_API_KEY", "").strip())


def _headers() -> dict:
    key = os.environ.get("AIRTABLE_API_KEY", "").strip()
    if not key:
        raise AirtableError(
            "AIRTABLE_API_KEY is not set — use `main.py copy-sync` with records "
            "fetched through the MCP instead"
        )
    return {"Authorization": f"Bearer {key}"}


def list_records(table: str, *, base_id: str = BASE_ID,
                 view: str | None = None) -> list[dict]:
    """Every record in a table, following pagination.

    Returns Airtable's own shape (`{"id": ..., "fields": {...}}`) untouched, so
    the caller reshapes once, in one place, rather than this module guessing.
    """
    records: list[dict] = []
    params: dict = {"pageSize": 100}
    if view:
        params["view"] = view
    url = f"{API_ROOT}/{base_id}/{requests.utils.quote(table)}"

    while True:
        try:
            response = requests.get(url, headers=_headers(), params=params,
                                    timeout=TIMEOUT)
        except requests.RequestException as exc:
            raise AirtableError(f"Airtable unreachable: {exc}") from exc

        if response.status_code == 401:
            raise AirtableError("Airtable rejected the key (401)")
        if response.status_code == 404:
            raise AirtableError(f"no table {table!r} in base {base_id}")
        if response.status_code != 200:
            raise AirtableError(
                f"Airtable returned {response.status_code}: {response.text[:200]}")

        payload = response.json()
        records.extend(payload.get("records", []))
        offset = payload.get("offset")
        if not offset:
            return records
        params["offset"] = offset


def copy_assets(base_id: str = BASE_ID) -> list[dict]:
    """The Copy Assets table, as flat field dicts."""
    return [record.get("fields", {})
            for record in list_records(COPY_ASSETS_TABLE, base_id=base_id)]


def update_records(table: str, updates: list[dict], *,
                   base_id: str = BASE_ID) -> int:
    """PATCH existing records. `updates` is [{"id": rec..., "fields": {...}}].

    Batched at 10, which is Airtable's per-request limit, and the reason this
    lives here rather than being open-coded at the call site.
    """
    if not updates:
        return 0
    url = f"{API_ROOT}/{base_id}/{requests.utils.quote(table)}"
    written = 0
    for start in range(0, len(updates), 10):
        chunk = updates[start:start + 10]
        try:
            response = requests.patch(url, headers={**_headers(),
                                                    "Content-Type": "application/json"},
                                      json={"records": chunk}, timeout=TIMEOUT)
        except requests.RequestException as exc:
            raise AirtableError(f"Airtable unreachable: {exc}") from exc
        if response.status_code != 200:
            raise AirtableError(
                f"Airtable returned {response.status_code}: {response.text[:200]}")
        written += len(response.json().get("records", []))
    return written


def create_records(table: str, records: list[dict], *,
                   base_id: str = BASE_ID) -> int:
    """POST new records. `records` is [{"fields": {...}}]. Batched at 10."""
    if not records:
        return 0
    url = f"{API_ROOT}/{base_id}/{requests.utils.quote(table)}"
    written = 0
    for start in range(0, len(records), 10):
        chunk = records[start:start + 10]
        try:
            response = requests.post(url, headers={**_headers(),
                                                   "Content-Type": "application/json"},
                                     json={"records": chunk}, timeout=TIMEOUT)
        except requests.RequestException as exc:
            raise AirtableError(f"Airtable unreachable: {exc}") from exc
        if response.status_code != 200:
            raise AirtableError(
                f"Airtable returned {response.status_code}: {response.text[:200]}")
        written += len(response.json().get("records", []))
    return written
