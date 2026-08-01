"""The retrieval ledger: one JSON line per fetch, written as the run proceeds.

Every cost claim ever made about this machine was reconstructed by hand from a
journal entry. The first real batch could not answer *which rung produced our
hooks* or *what did the leads that produced nothing cost us*, because nothing
recorded either. `estimate_cost_usd` was the only function in the repo that
produced a dollar figure, and it was computed, compared against the approval
threshold, and thrown away — surviving only inside the exception raised when the
gate refused. `batch_fetch`'s `elapsed_secs` was the only clock, and it was
batch-wide.

So: one append per retrieval, at the moment it happens, to
`data/runs/<batch>.jsonl`. Written as the run proceeds rather than at the end,
so a batch that dies in stage 3 still leaves its accounting behind.

Three decisions worth not re-litigating.

**`append` never raises.** This is the only thing in this repo whose default is
the opposite of every gate, and the exception is the point: an observer that can
halt the thing it observes is worse than no observer. A ledger write failing
must not be able to kill a batch that was otherwise going to ship.

**A missing ledger is exit 2, not zero.** Same asymmetry as the dedupe wall. A
missing wall must never read as "nobody has been contacted"; a missing ledger
must never read as "this batch cost nothing".

**`purpose` is what makes the retrieve-once invariant checkable.** The rule the
proposal argues for is that information is retrieved exactly once per (lead,
source), and the only permitted second fetch is a verification — which must be a
live fetch, because a verifier reading a cache is certifying the cache. So a
second record for the same `(lead_key, url)` that is not `purpose="verify"` is a
duplicate, and `summarise` names it. **It does not fail on one.** Making the
invariant blocking belongs with the stage that removes the duplicate; a gate
that can halt a real send file over an accounting line is a gate people learn to
route around.

The costs here are Apify's own **estimates**, not billed amounts. The runner
uses `run-sync-get-dataset-items`, which collapses a run to its output, so
`usageTotalUsd` is never fetched. A ledger that implied otherwise would be worse
than none.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict, fields as dataclass_fields
from datetime import date, datetime, timezone
from pathlib import Path

RUNS_DIR = "data/runs"

PURPOSES = ("observe", "verify")
OUTCOMES = ("ok", "empty", "error", "blocked")

# The free rungs record themselves through the CLI, on trust: an agent's own
# WebSearch and WebFetch happen model-side and are invisible to Python. Keeping
# them distinguishable in `retrieved_by` is what stops the ledger from claiming
# an authority over tier 1 it does not have.
REPORTED_BY = ("websearch", "webfetch")

_lock = threading.Lock()

# Process-scoped. One CLI invocation is one retrieval context — this is a
# command, not a server. `audit/apify.py` knows the technical facts of a fetch
# (which actor, which URL, how long, what it was priced at); only the caller
# knows the run facts (which lead, which stage, observe or verify).
_context: dict[str, str] = {}


class LedgerUnreadable(RuntimeError):
    """The ledger could not be read. Always exit 2, never an empty report."""


@dataclass
class Retrieval:
    """One fetch. The unit is (lead, source), not lead."""

    lead_key: str = ""
    stage: str = ""              # fetch | resolve | research | hook | verify | email
    platform: str = ""           # site | linkedin | instagram | youtube | linkinbio | web | email
    url: str = ""
    retrieved_by: str = ""       # tier0 | websearch | webfetch | apify:<actor_key>
    cost_usd: float | None = 0.0  # None when the actor could not be priced
    secs: float = 0.0
    outcome: str = "ok"          # ok | empty | error | blocked
    purpose: str = "observe"     # observe | verify
    at: str = ""                 # ISO timestamp, stamped by append()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Retrieval":
        known = cls.__dataclass_fields__
        return cls(**{k: v for k, v in data.items() if k in known})


# ------------------------------------------------------------------- context


def set_context(**values: str) -> None:
    """Set the run facts for this process. Blank values are ignored, so a
    command that has no lead does not blank one an earlier call set."""
    for key, value in values.items():
        if value:
            _context[key] = str(value)


def get_context() -> dict:
    return dict(_context)


def clear_context() -> None:
    _context.clear()


# --------------------------------------------------------------------- paths


def batch_label(batch: str | None = None) -> str:
    """The batch this run belongs to. `OUTBOUND_BATCH` if set, else today —
    the same default `export --batch` already uses, so a batch's ledger and its
    upload file carry the same label without anyone passing it twice."""
    return (batch or os.environ.get("OUTBOUND_BATCH")
            or date.today().isoformat())


def path(batch: str | None = None, root: str | Path | None = None) -> Path:
    """Where this batch's ledger lives.

    `OUTBOUND_LEDGER_ROOT` redirects the whole thing, which is what the test
    suite uses — the same shape as `OUTBOUND_COPY_SOURCE=csv`. Without it a
    test that exercised `batch_fetch` would append real lines to the real
    repo's ledger, and the first honest cost figure this machine produces would
    have a test run mixed into it.
    """
    base = Path(root or os.environ.get("OUTBOUND_LEDGER_ROOT")
                or Path(__file__).resolve().parent.parent)
    return base / RUNS_DIR / f"{batch_label(batch)}.jsonl"


# --------------------------------------------------------------------- write


def append(record: Retrieval, *, batch: str | None = None,
           root: str | Path | None = None) -> bool:
    """Append one retrieval. Returns whether it was written; NEVER raises.

    Every other check in this repo fails closed. This one fails open, on
    purpose — see the module docstring. The return value exists so a test can
    assert the difference between "wrote it" and "swallowed it", which is the
    only way a silent no-op stays honest.
    """
    try:
        if not record.at:
            record.at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = json.dumps(record.to_dict(), ensure_ascii=False, default=str)
        target = path(batch, root)
        with _lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return True
    except Exception:
        return False


def record(*, batch: str | None = None, root: str | Path | None = None,
           **values) -> bool:
    """Build a Retrieval from the ambient context plus what the caller knows,
    and append it. The caller's values win — the context is a default, not an
    override, or a stage label set once would outrank the truth."""
    known = {f.name for f in dataclass_fields(Retrieval)}
    fields = {k: v for k, v in get_context().items() if k in known}
    fields.update({k: v for k, v in values.items() if k in known})
    return append(Retrieval(**fields), batch=batch, root=root)


# ---------------------------------------------------------------------- read


def read(batch: str | None = None,
         root: str | Path | None = None) -> tuple[list[Retrieval], int]:
    """(records, malformed line count). Raises LedgerUnreadable on a missing
    or unopenable file.

    A malformed line is skipped and counted rather than fatal: the ledger is
    appended to as a run proceeds, so a batch killed mid-write legitimately
    leaves a half-written last line. Losing the other 400 records to it would
    defeat the reason for writing them as we go.
    """
    target = path(batch, root)
    if not target.is_file():
        raise LedgerUnreadable(
            f"no ledger at {target} — a missing ledger is not a zero-cost batch")
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise LedgerUnreadable(f"cannot read {target}: {type(exc).__name__}") from exc

    records, malformed = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except ValueError:
            malformed += 1
            continue
        if isinstance(data, dict):
            records.append(Retrieval.from_dict(data))
        else:
            malformed += 1
    return records, malformed


# ------------------------------------------------------------------ analysis


def duplicates(records: list[Retrieval]) -> list[dict]:
    """Second and later fetches of the same (lead, url) that are not a verify.

    The invariant, stated once: information is retrieved exactly once per lead
    per source, and the only permitted second fetch is a verification. A
    verifier's fetch is not overhead, it is the product — it is the one thing in
    this system that has actually caught a fabricated claim — so it is exempt
    here rather than merely tolerated.
    """
    seen: dict[tuple[str, str], Retrieval] = {}
    out = []
    for entry in sorted(records, key=lambda r: r.at):
        if not entry.url:
            continue
        key = (entry.lead_key, entry.url)
        first = seen.get(key)
        if first is None:
            seen[key] = entry
            continue
        if entry.purpose == "verify":
            continue
        out.append({
            "lead_key": entry.lead_key,
            "url": entry.url,
            "first": f"{first.stage or '?'} via {first.retrieved_by or '?'}",
            "again": f"{entry.stage or '?'} via {entry.retrieved_by or '?'}",
            "cost_usd": entry.cost_usd or 0.0,
        })
    return out


def _total(records: list[Retrieval]) -> float:
    return round(sum(r.cost_usd or 0.0 for r in records), 4)


def summarise(records: list[Retrieval]) -> dict:
    """Totals, breakdowns, per-lead cost, and the duplicate fetches."""
    by_source: dict[str, dict] = {}
    by_stage: dict[str, dict] = {}
    by_lead: dict[str, dict] = {}
    for entry in records:
        for bucket, key in ((by_source, entry.retrieved_by or "?"),
                            (by_stage, entry.stage or "?"),
                            (by_lead, entry.lead_key or "?")):
            slot = bucket.setdefault(key, {"n": 0, "cost_usd": 0.0, "secs": 0.0})
            slot["n"] += 1
            slot["cost_usd"] = round(slot["cost_usd"] + (entry.cost_usd or 0.0), 4)
            slot["secs"] = round(slot["secs"] + (entry.secs or 0.0), 1)

    unpriced = [r for r in records if r.cost_usd is None]
    return {
        "count": len(records),
        "cost_usd": _total(records),
        "secs": round(sum(r.secs or 0.0 for r in records), 1),
        "leads": len({r.lead_key for r in records if r.lead_key}),
        "unpriced": len(unpriced),
        "blocked": sum(1 for r in records if r.outcome == "blocked"),
        "errors": sum(1 for r in records if r.outcome == "error"),
        "by_source": by_source,
        "by_stage": by_stage,
        "by_lead": by_lead,
        "duplicates": duplicates(records),
    }


def report(records: list[Retrieval], *, batch: str | None = None,
           malformed: int = 0, leads: int = 0) -> str:
    """The block a skill quotes. `leads` is the batch's real lead count when the
    caller knows it, so cost-per-lead is not silently computed over only the
    leads that happened to need a fetch."""
    stats = summarise(records)
    denominator = leads or stats["leads"]
    per_lead = (stats["cost_usd"] / denominator) if denominator else 0.0

    lines = [
        f"LEDGER {batch_label(batch)}: {stats['count']} retrieval(s), "
        f"${stats['cost_usd']:.4f} est over {stats['leads']} lead(s), "
        f"{stats['secs']:.0f}s",
        f"  ${per_lead:.4f}/lead"
        + (f" over {denominator} lead(s)" if denominator else ""),
    ]
    for source, slot in sorted(stats["by_source"].items()):
        lines.append(f"  {source:24} {slot['n']:4} call(s)  "
                     f"${slot['cost_usd']:.4f}  {slot['secs']:.0f}s")
    if stats["by_stage"]:
        lines.append("  by stage: " + ", ".join(
            f"{stage} {slot['n']}" for stage, slot in sorted(stats["by_stage"].items())))
    if stats["unpriced"]:
        lines.append(f"  {stats['unpriced']} run(s) could not be priced — "
                     f"compute-billed actors are not a lookup failure")
    if stats["blocked"]:
        lines.append(f"  {stats['blocked']} run(s) BLOCKED by the cost gate")
    if stats["errors"]:
        lines.append(f"  {stats['errors']} retrieval(s) errored")
    for dupe in stats["duplicates"]:
        lines.append(f"  DUPLICATE  {dupe['lead_key'] or '?'}  {dupe['url']}  "
                     f"{dupe['first']} then {dupe['again']}")
    if not stats["duplicates"]:
        lines.append("  no duplicate fetch: every (lead, url) retrieved once, "
                     "or again only to verify")
    if malformed:
        lines.append(f"  {malformed} unreadable line(s) skipped — a run that "
                     f"died mid-write leaves one")
    return "\n".join(lines)
