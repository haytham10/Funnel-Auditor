"""Direct Airtable REST reads, for when a key exists.

Airtable reaches this repo two ways, and the difference matters:

- **Through the MCP**, which is the *model's* tool. Python cannot call it. A
  skill fetches records and hands them to `main.py copy-sync` on stdin.
- **Through this module**, which needs `AIRTABLE_API_KEY` in the environment.
  A Claude Code session has one, so this is the normal path, not a someday path.

Both land in the same place. `outbound/copy_sync.py` validates and writes a
snapshot; `outbound/anchors.py` reads it. The point of two paths is that a run
without a key still works, and that nothing silently half-works when it happens:
`available()` is False, the caller falls through to the snapshot and then to the
CSVs, and it records why — `main.py copy-check` asserts the live path and `deal`
refuses a whole batch drawn from a cache nobody just checked.

Reads are unrestricted. Writes are deliberately narrow: `update_records` exists
so a finished batch can report usage back to Copy Assets, which is the only way
the weights ever stop being guesses. Nothing here creates or deletes a table,
and nothing writes a Lead — that stays in the skill layer where a human sees it.

**`outbound/crm.py` builds the Leads row and still does not write it**, which is
the same boundary rather than a hole in it. The push that went wrong on
`2026-08-01-q1` was not wrong because a model did the typing; it was wrong
because a model did the *join*, from memory, in a script nothing tested, and
twenty rows landed with five columns empty and no error. Computing in code and
writing by hand puts each half where it can fail visibly.
"""

from __future__ import annotations

import os

import requests

API_ROOT = "https://api.airtable.com/v0"
META_ROOT = "https://api.airtable.com/v0/meta/bases"
TIMEOUT = 20

# The live base. Recorded here rather than passed in, because a typo'd base ID
# that silently reads the wrong table is worse than a missing key.
BASE_ID = "appejF07kunksqt4D"
COPY_ASSETS_TABLE = "Copy Assets"
# The other two tables the machine writes. Named here rather than hardcoded in a
# skill, so a rename is one edit and the ids stay next to the base they belong to.
LEADS_TABLE = "Leads"
BATCHES_TABLE = "Batches"

# Single-select fields reject a value outside their option list, and the write
# fails at the CRM step — after the email is already in the upload file. These
# mirror the live base so a bad value is caught before it gets that far.
#
# They are a copy of a schema this repo does not own, which is the one place the
# rest of the value-ownership rule cannot reach: somebody adds an option in the
# Airtable UI and nothing here notices. `main.py doc-check --live` closes that
# by fetching `base_schema()` and comparing, so the freshness of these tuples is
# a check rather than the date on this comment.
HOOK_TYPES = ("WORK", "LIFE", "METRIC")
HOOK_VERIFIED = ("verified", "proposed", "refuted", "inconclusive", "none")
EMAIL_STATUSES = ("pass", "enriched", "warn", "fail", "none")
LEAD_STATUSES = ("Sourced", "Researching", "Qualified", "Drafted", "Exported",
                 "Held", "Disqualified")
FAILED_FLOORS = ("Not UAE-based", "Not a coach", "Inactive 30d")
SELLS_TO = ("corporates", "individuals")
SOLO = ("yes", "no", "unclear")


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


def base_schema(base_id: str = BASE_ID) -> dict:
    """Every table in the base, with each field's type and its select choices.

    Needs `schema.bases:read` on the token, which is a *different* scope from
    the record reads above. A token granted only record access works everywhere
    else in this module and 403s here, so that case names the missing scope
    rather than reporting a bare "forbidden" that reads like a wrong key.

    Returns Airtable's own shape untouched. `select_options` does the reshaping.
    """
    url = f"{META_ROOT}/{base_id}/tables"
    try:
        response = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise AirtableError(f"Airtable unreachable: {exc}") from exc

    if response.status_code == 401:
        raise AirtableError("Airtable rejected the key (401)")
    if response.status_code == 403:
        raise AirtableError(
            "Airtable refused the base schema (403) — the token needs the "
            "schema.bases:read scope, which record access does not include")
    if response.status_code == 404:
        raise AirtableError(f"no base {base_id}")
    if response.status_code != 200:
        raise AirtableError(
            f"Airtable returned {response.status_code}: {response.text[:200]}")

    payload = response.json()
    if not payload.get("tables"):
        raise AirtableError(f"base {base_id} reports no tables")
    return payload


def select_options(schema: dict, table: str, field: str) -> tuple:
    """The choice names of one select field, in the base's own order.

    A missing table, a missing field or a field that is not a select is an
    error, never an empty tuple. An empty option list would compare equal to a
    tuple of nothing and read as "no drift" — the same failure as an unreadable
    dedupe wall reading as "nobody has been contacted".
    """
    for entry in schema.get("tables", []):
        if entry.get("name") != table:
            continue
        for spec in entry.get("fields", []):
            if spec.get("name") != field:
                continue
            if spec.get("type") not in ("singleSelect", "multipleSelects"):
                raise AirtableError(
                    f"{table}.{field} is a {spec.get('type')}, not a select")
            choices = spec.get("options", {}).get("choices", [])
            if not choices:
                raise AirtableError(f"{table}.{field} reports no choices")
            return tuple(c["name"] for c in choices)
        raise AirtableError(f"no field {field!r} in {table}")
    raise AirtableError(f"no table {table!r} in the base schema")


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


# There is deliberately no `create_records` here.
#
# One existed from the day `update_records` was written, was never called by
# anything, and had no test. It was a generic POST, so `create_records(
# LEADS_TABLE, rows)` would have written Lead rows from Python — the one thing
# the docstring above says this module does not do — and it sat two screens
# below the constant naming that table. Nothing was wrong with the code; the
# problem was that the boundary was a sentence in a docstring while the capacity
# to cross it was right there, untested, waiting for a session in a hurry.
#
# `outbound/crm.py` builds the Leads rows and stops. A human writes them. That
# is the boundary, and the absence of a writer is what enforces it. Same rule as
# `audit/apify.py`'s: an actor is surface area, not capability.
