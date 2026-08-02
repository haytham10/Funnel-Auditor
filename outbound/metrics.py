"""What a batch's hook stage yielded, and what it cost to get there.

Part 8 of docs/proposals/2026-08-01-hook-retrieval.md names seven per-batch
numbers and this repo computed none of them. `ledger report` covers everything
Python can *see* — retrievals, cost, seconds, duplicates — because those pass
through code. Everything on the hook side happens in an agent, so it was
narrated into a batch brief by a model and then lost when the session ended.

That is F12 one layer up from where it was fixed. The ledger stopped the run
being uncostable; this stops it being unjudgeable. **The first real batch could
not answer "which rung produced our hooks" or "what did the leads that produced
nothing cost us", and those should be answerable before anybody tries to make
the stage better.**

## The rule that shapes every field here

**A count nobody supplied prints `?`, never `0`.** This is the wall's asymmetry
and the ledger's, applied a third time: a missing wall must never read as
"nobody has been contacted", a missing ledger must never read as "this batch
cost nothing", and an unsupplied raw count must never read as "no leads came
in". A zero is a measurement. `?` is the honest word for a thing not measured,
and a metrics block that quietly zero-fills is worse than no block, because it
looks like evidence.

So this command takes the counts it cannot derive as explicit inputs and prints
`?` for each one it was not given. It never reaches back into a stage to guess.

## It never exits 1

Same argument as the ledger, and worth restating because it is the reason this
is safe to wire into a real run: **a gate that can halt a send file over an
accounting line is a gate people learn to route around.** Reporting a bad
number is the job; failing on one is not. Exit 2 when it could not read its
inputs at all, which is the ledger's rule and the wall's — a batch whose
metrics could not be computed must not report as a batch with no findings.

## `yield_by_rung` is the one that settles F5

F5 says the cheapest rung produces the observations most likely to be refuted:
`hook-verifier` refutes anything that "could be sent unedited to another coach
in the same segment", and generic About prose is exactly that. So an agent
walking the ladder honestly spends rung 1, gets refuted, and walks to the paid
rungs anyway. Part 8 calls `yield_by_rung` "the number that fixes F5", because
it turns that from an argument into a count: if rung 1 yields near zero after
verification, narrowing it is proven rather than reasoned.

The rung a hook came from is derived from its source URL rather than reported,
so a worker cannot mislabel it. `plan.LADDER` owns which platforms belong to
which rung and `normalize.classify_site` owns which host is which platform —
neither is restated here (D23).

## What is reported on trust, and why it is marked

`agent_passes` cannot be seen from Python. Agent passes happen in the main loop,
the same blind spot that makes a research worker's own WebSearch invisible to
the ledger. The ledger's answer is `ledger add`: record it, and keep it
distinguishable from what the code measured. This does the same — `--passes` is
carried through and labelled `reported`, so nobody reads a number an orchestrator
typed as one the machine counted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

# The hook stage's four outcomes, from `outbound/research.py`. Named rather than
# re-derived so a fifth verdict cannot appear here without appearing there.
HOOK_STATES = ("verified", "refuted", "proposed", "none")

# A count this command was not given. Not 0, and not "" — printed and stored, so
# the distinction survives into `data/runs/<batch>-metrics.json` rather than
# living only in the terminal.
UNKNOWN = "?"


@dataclass
class BatchMetrics:
    """One batch, judged. Every ratio is None when its denominator is zero."""

    batch: str = ""

    # --- the hook stage, derived from the research objects -----------------
    leads: int = 0
    attempted: int = 0              # leads a hook was actually sought for
    verified: int = 0
    refuted: int = 0
    proposed: int = 0               # never reached a verifier
    none_found: int = 0             # the null answer, which is a good one
    hook_yield: float | None = None
    refute_rate: float | None = None
    null_hook_rate: float | None = None
    yield_by_rung: dict = field(default_factory=dict)
    by_hook_type: dict = field(default_factory=dict)
    # The flip's own number (D27). A hook with no `observation_id` is one the
    # worker had to go and fetch because the shortlist did not hold, and rising
    # means selection is not reaching the material — which points at research
    # fetching deeper, not at the ranker. R1, made countable.
    escalated: int = 0
    escalation_rate: float | None = None

    # --- D21's reversal condition, computable at last ----------------------
    # Of the leads carrying a declined rung, how many produced a verified hook
    # and how many produced none. `None` for both when no plan was passed: a
    # zero here would read as "declining cost nothing", which is the claim the
    # number exists to test.
    declined_leads: object = UNKNOWN
    declined_and_verified: object = UNKNOWN
    declined_and_dry: object = UNKNOWN

    # --- cost, derived from the ledger -------------------------------------
    # `ledger_read` is what keeps $0.0000 from meaning two different things. A
    # batch that genuinely spent nothing and a batch whose ledger was never
    # opened are the same number and opposite facts, and the second must never
    # reach the CRM's cost field as a zero. Same asymmetry as everything else
    # here, at the one field where a wrong zero is most expensive to believe.
    ledger_read: bool = False
    retrievals: int = 0
    cost_usd: float = 0.0
    unpriced: int = 0
    cost_per_verified_hook: float | None = None
    wasted_retrieval_n: int = 0
    wasted_retrieval_usd: float = 0.0
    duplicates: int = 0

    # --- counts only an earlier stage knows. `?` until supplied ------------
    raw: object = UNKNOWN
    after_dedupe: object = UNKNOWN
    warm: object = UNKNOWN
    passed_floors: object = UNKNOWN
    written: object = UNKNOWN
    rejected: object = UNKNOWN
    tier0_rate: object = UNKNOWN
    source_list: object = UNKNOWN
    agent_passes: object = UNKNOWN   # reported on trust, never measured
    # The same trust, kept per stage and per model, because one scalar could not
    # answer the question anybody actually asks about the Claude bill: which
    # stage is it, and is it running on the tier it needs? `2026-08-01-q1` cost
    # ~64 passes for 20 leads and 5 rows, and "the drafting loop is most of it"
    # was a guess. Empty means nothing was reported — `?`, never 0.
    passes_by_stage: dict = field(default_factory=dict)
    passes_by_model: dict = field(default_factory=dict)

    # --- what could not be computed, named rather than left as a zero ------
    gaps: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _ratio(numerator: int, denominator: int) -> float | None:
    """None, not 0.0, when there is nothing to divide by.

    Zero of zero hooks is not a 0% yield — it is a batch that never asked. The
    report prints `?` for None, and that difference is the whole point of the
    module.
    """
    if not denominator:
        return None
    return round(numerator / denominator, 3)


def rung_of(url: str) -> str:
    """Which ladder rung a hook at this URL came from.

    Derived, never reported. A worker naming its own rung is a worker that can
    mislabel the number judging its rung, which is the same reason `select`
    derives the `obs_id` join rather than trusting a citation.

    `plan.LADDER` owns the rungs and their platforms; `normalize.classify_site`
    owns which host is which platform. Neither is restated here — D23 exists
    because this stage already had the same value copied into four files.

    **One platform can carry two rungs.** LinkedIn does: a profile and a post
    are different actors at different prices, one batchable and one not. While
    LADDER had a single LinkedIn rung this function reported `li_posts 10` on a
    batch where three of those hooks came off profiles — and `yield_by_rung` is
    the number that settles F5, so the rung it names has to be the rung that was
    walked. The URL shape decides, from `Rung.url_marks`.
    """
    from outbound.plan import LADDER
    from outbound.resolve import _platform_of

    if not (url or "").strip():
        return "none"
    # A URL on nobody's platform is their own site, which is rung `about`.
    platform = _platform_of(url) or "site"
    candidates = [rung for rung in LADDER if platform in rung.platforms]
    if not candidates:
        return "other"
    lowered = url.lower()
    for rung in candidates:
        if any(mark in lowered for mark in rung.url_marks):
            return rung.name
    # No mark matched. Falling back to the first candidate would silently
    # re-create the conflation this function exists to end, so an ambiguous URL
    # on a multi-rung platform says so instead of picking.
    if len(candidates) > 1:
        return f"{platform}_unattributed"
    return candidates[0].name


def from_research(rows: list, *, batch: str = "") -> BatchMetrics:
    """The hook-side half, from the objects the research and hook stages left.

    `attempted` deliberately excludes a lead that never reached the hook stage.
    A lead dropped at the floors did not produce a null hook — it produced no
    attempt — and folding the two together would make `null_hook_rate` a
    function of how many leads failed the ICP, which is a different question
    with a different answer.
    """
    out = BatchMetrics(batch=batch, leads=len(rows))

    for row in rows:
        state = (row.get("hook_verified") or "").strip().lower()
        has_hook = bool((row.get("hook") or "").strip())
        # A lead that never reached the stage carries no verdict at all.
        if state not in HOOK_STATES:
            continue
        out.attempted += 1
        # Post-flip a hook either names the observation it was selected from or
        # is one the worker escalated to get. Counted over every attempt rather
        # than only the verified ones: an escalation that produced a refuted
        # hook still cost the fetch the flip was meant to remove.
        if has_hook and not (row.get("observation_id") or "").strip():
            out.escalated += 1
        if state == "verified":
            out.verified += 1
            name = rung_of(row.get("hook_source_url") or "")
            slot = out.yield_by_rung.setdefault(name, {"verified": 0})
            slot["verified"] += 1
            kind = (row.get("hook_type") or "?").strip().upper() or "?"
            out.by_hook_type[kind] = out.by_hook_type.get(kind, 0) + 1
        elif state == "refuted":
            out.refuted += 1
        elif state == "none" or not has_hook:
            out.none_found += 1
        else:
            out.proposed += 1

    out.hook_yield = _ratio(out.verified, out.attempted)
    out.refute_rate = _ratio(out.refuted, out.attempted)
    out.null_hook_rate = _ratio(out.none_found, out.attempted)
    out.escalation_rate = _ratio(out.escalated, out.attempted)
    return out


def add_plan(out: BatchMetrics, plans: list, rows: list) -> BatchMetrics:
    """D21's reversal condition, in its own words, finally computable.

    *"A batch where declining to spend on low-confidence channels costs more
    verified hooks than it saves scrapes."* The gate binds as of D27, and a gate
    whose evidence nobody collects is exactly what `plan` spent two batches
    refusing to become.

    The join is on `lead_key`, and a declined lead with no research object is
    skipped rather than counted as dry: it never reached the hook stage, so it
    says nothing about whether the decline cost anything. Counting it would
    charge the gate for a lead the floors dropped.
    """
    if not plans:
        return out

    declined = {(p.get("lead_key") or "").strip()
                for p in plans
                if any((s.get("decision") or "") == "decline"
                       for s in (p.get("steps") or []))}
    declined.discard("")

    out.declined_leads = len(declined)
    out.declined_and_verified = 0
    out.declined_and_dry = 0
    for row in rows or []:
        key = (row.get("lead_key") or row.get("email") or "").strip()
        if key not in declined:
            continue
        state = (row.get("hook_verified") or "").strip().lower()
        if state not in HOOK_STATES:
            continue
        if state == "verified":
            out.declined_and_verified += 1
        else:
            out.declined_and_dry += 1
    return out


def add_passes(out: BatchMetrics, entries: list) -> BatchMetrics:
    """The model-side half, reported on trust and labelled as such.

    Kept out of `add_ledger` because the two have different authorities: those
    records were written by code at the moment of a fetch, these were typed by
    an orchestrator. Folding them into one call would make it easy to print them
    with the same confidence, and the whole point of `REPORTED` is that they do
    not have it.
    """
    from outbound.ledger import passes_by

    out.passes_by_stage = passes_by(entries, "stage")
    out.passes_by_model = passes_by(entries, "model")
    if entries and out.agent_passes is UNKNOWN:
        # A total nobody typed, derived from parts somebody did. Still REPORTED
        # — the sum of trusted numbers is a trusted number, not a measured one.
        out.agent_passes = sum(out.passes_by_stage.values())
    return out


def add_ledger(out: BatchMetrics, records: list, *, verified_leads: set) -> BatchMetrics:
    """The cost half, and the one number this whole proposal set out to move.

    **`wasted_retrieval` is paid fetches on leads that produced no verified
    hook.** Free rungs are excluded deliberately: tier 0 and an agent's own
    WebSearch cost nothing, so counting them would inflate a figure whose entire
    use is deciding whether a *purchase* was worth making. A verification fetch
    is excluded for the same reason — it is spent on a hook that exists, and it
    is the one duplicate this machine wants.
    """
    from outbound.ledger import duplicates, summarise

    stats = summarise(records)
    out.ledger_read = True
    out.retrievals = stats["count"]
    out.cost_usd = stats["cost_usd"]
    out.unpriced = stats["unpriced"]
    out.duplicates = len(duplicates(records))
    out.cost_per_verified_hook = (
        round(out.cost_usd / out.verified, 4) if out.verified else None)

    for entry in records:
        paid = (entry.retrieved_by or "").startswith("apify:")
        if not paid or entry.purpose == "verify":
            continue
        if entry.lead_key and entry.lead_key in verified_leads:
            continue
        out.wasted_retrieval_n += 1
        out.wasted_retrieval_usd = round(
            out.wasted_retrieval_usd + (entry.cost_usd or 0.0), 4)

    if stats["unpriced"]:
        out.gaps.append(
            f"{stats['unpriced']} run(s) could not be priced — compute-billed "
            f"actors are not a lookup failure, so the cost figures are a floor")
    return out


def _pct(value) -> str:
    return UNKNOWN if value is None else f"{value * 100:.0f}%"


def _num(value) -> str:
    return UNKNOWN if value is UNKNOWN or value is None else str(value)


def report(out: BatchMetrics) -> str:
    """The block a skill quotes. Ratios print `?` where nothing was attempted."""
    lines = [
        f"METRICS {out.batch or 'unlabelled'}: {out.leads} lead(s), "
        f"{out.attempted} hook attempt(s)",
        f"  hook_yield        {_pct(out.hook_yield)}  "
        f"({out.verified} verified of {out.attempted} attempted)",
        f"  refute_rate       {_pct(out.refute_rate)}  ({out.refuted} refuted)",
        f"  null_hook_rate    {_pct(out.null_hook_rate)}  "
        f"({out.none_found} found nothing — a good answer, not a failure)",
    ]
    # The one shape these ratios cannot be trusted in. `hook_verified`,
    # `hook_type`, `hook_source_url` and `observation_id` are written back onto
    # the lead rows at stage 3b, by the orchestrator, by hand — nothing in
    # Python can do it, because the verdict lives in an agent. Skip that step
    # and every count above is computed from the research worker's defaults:
    # `hook_yield 0%` and `null_hook_rate 100%` on a batch that shipped verified
    # hooks, and a `Hooks Verified 0` that goes into the CRM as a measurement.
    #
    # That is the `?`-not-`0` rule defeated from underneath. The rule protects a
    # count nobody supplied; this one *was* supplied, from a field nobody was
    # told to update, so it prints as evidence. `written` is the cross-check
    # because it comes from `export`, which counted rows it actually wrote.
    if isinstance(out.written, int) and out.written > 0 and out.verified == 0:
        lines.append(
            f"  SUSPECT           {out.written} email(s) were written and 0 "
            f"hook(s) read as verified. An exported email has a verified hook "
            f"by construction, so the likely cause is the stage 3b write-back: "
            f"put hook_verified / hook_type / hook_source_url / observation_id "
            f"back on the lead rows and re-run. Every ratio above is computed "
            f"from those fields and is wrong until you do")
    lines.append(
        f"  escalation_rate   {_pct(out.escalation_rate)}  "
        f"({out.escalated} hook(s) the shortlist did not hold)")
    lines.append("                    D27's number. Rising means selection is "
                 "not reaching the material, and the fix is research fetching "
                 "deeper rather than a change to the ranker")
    if out.proposed:
        lines.append(f"  proposed          {out.proposed} never reached a verifier")

    if out.yield_by_rung:
        lines.append("  yield_by_rung     "
                     + ", ".join(f"{name} {slot['verified']}"
                                 for name, slot in sorted(out.yield_by_rung.items())))
        lines.append("                    the number that settles F5: a rung "
                     "yielding near zero after verification is narrowed on "
                     "evidence rather than argument")
    else:
        lines.append("  yield_by_rung     no verified hook to attribute")

    if out.by_hook_type:
        lines.append("  by_hook_type      "
                     + ", ".join(f"{k} {v}" for k, v in sorted(out.by_hook_type.items())))

    # D21's reversal condition. `?` rather than 0 when no plan was passed: a
    # zero here would read as "declining cost nothing", which is the claim.
    if out.declined_leads is UNKNOWN:
        lines.append(f"  declined_and_dry  {UNKNOWN}  no plan read — pass "
                     f"--plan work/plan.json. This is D21's reversal condition "
                     f"and the gate binds now, so a batch without it is a gate "
                     f"running with nobody collecting its evidence")
    else:
        lines.append(
            f"  declined_and_dry  {out.declined_and_dry} of "
            f"{out.declined_leads} lead(s) with a declined rung produced no "
            f"verified hook ({out.declined_and_verified} did)")
        lines.append("                    declining is free where these are the "
                     "same leads and wrong where they are not — D21's reversal "
                     "condition, in its own words")

    if out.ledger_read:
        lines += [
            f"  cost_per_hook     "
            + (UNKNOWN if out.cost_per_verified_hook is None
               else f"${out.cost_per_verified_hook:.4f}")
            + f"  (${out.cost_usd:.4f} over {out.retrievals} retrieval(s))",
            f"  wasted_retrieval  {out.wasted_retrieval_n} paid fetch(es), "
            f"${out.wasted_retrieval_usd:.4f} on leads that produced no "
            f"verified hook",
        ]
    else:
        lines += [
            f"  cost_per_hook     {UNKNOWN}  no ledger read",
            f"  wasted_retrieval  {UNKNOWN}  no ledger read — this is the "
            f"number the whole proposal set out to move, so a run without it "
            f"is not a judged batch",
        ]
    lines.append(
        f"  agent_passes      {_num(out.agent_passes)}"
        + ("" if out.agent_passes is UNKNOWN else " — REPORTED, not measured"))
    # The Claude bill, and the reason it is here at all: retrieval had a ledger
    # and the model side had one number typed at the end of a long session.
    if out.passes_by_stage:
        lines.append("  passes_by_stage   "
                     + ", ".join(f"{k} {v}" for k, v in out.passes_by_stage.items())
                     + " — REPORTED, not measured")
    else:
        lines.append(f"  passes_by_stage   {UNKNOWN}  nothing reported "
                     f"(`ledger pass --stage <s> --model <m>`)")
    if out.passes_by_model:
        lines.append("  passes_by_model   "
                     + ", ".join(f"{k} {v}" for k, v in out.passes_by_model.items())
                     + " — REPORTED, not measured")
    else:
        lines.append(f"  passes_by_model   {UNKNOWN}  nothing reported")
    if out.duplicates:
        lines.append(f"  duplicates        {out.duplicates} — quote "
                     f"`ledger report` for which")
    for gap in out.gaps:
        lines.append(f"  GAP  {gap}")
    lines.append("  OBSERVER. This never fails a batch: reporting a bad number "
                 "is the job, and a gate that can halt a send file over an "
                 "accounting line gets routed around.")
    return "\n".join(lines)


# The Batches table's field names, exactly as the CRM spells them, paired with
# where each value comes from. Airtable owns these names; this list mirrors them
# and `doc-check` is what catches the mirror going stale.
BATCH_FIELDS = (
    ("Batch", "batch"),
    ("Source List", "source_list"),
    ("Raw Count", "raw"),
    ("After Dedupe", "after_dedupe"),
    ("Warm Hits", "warm"),
    ("Passed Floors", "passed_floors"),
    ("Hooks Verified", "verified"),
    ("Written", "written"),
    ("Rejected", "rejected"),
    ("Tier 0 Rate", "tier0_rate"),
    ("Apify Cost USD", "cost_usd"),
)


def batches_block(out: BatchMetrics) -> str:
    """The Batches row, computed here and written by a human-visible step.

    **This prints; it does not write.** `audit/airtable.py` states the boundary
    it keeps — writes stay narrow, and a row lands where a human sees it — and
    a metrics command is not the place to widen that. What was actually wrong
    was never that a model did the typing: it was that a model did the
    *arithmetic*, from memory, at the end of a long run. Every number below is
    measured or `?`, so transcription is all that is left to get wrong.
    """
    lines = [f"BATCHES ROW — paste into Airtable, {len(BATCH_FIELDS)} field(s):"]
    unknown = []
    for label, attr in BATCH_FIELDS:
        value = getattr(out, attr)
        # Cost is only a number when a ledger was actually read. $0.0000 from an
        # unopened ledger is the one wrong zero that would land in the CRM and
        # be believed for months.
        if attr == "cost_usd":
            shown = f"{value:.4f}" if out.ledger_read else UNKNOWN
        elif attr == "tier0_rate" and value is not UNKNOWN:
            shown = f"{float(value) * 100:.0f}%"
        else:
            shown = _num(value)
        if shown == UNKNOWN:
            unknown.append(label)
        lines.append(f"  {label:16} {shown}")
    if unknown:
        lines.append(f"  {len(unknown)} field(s) are ? — NOT zero. Pass the "
                     f"stage that owns each, or leave the cell empty: "
                     + ", ".join(unknown))
    return "\n".join(lines)


def write_artifact(out: BatchMetrics, path: str | Path) -> Path:
    """Persist the block, because a number that lived only in a terminal is the
    reason Part 2's cost claims had to be reconstructed from a journal entry."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out.to_dict(), indent=2, default=str),
                      encoding="utf-8")
    return target
