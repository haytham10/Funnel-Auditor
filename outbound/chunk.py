"""An enriched list -> the chunks a batch actually runs, and the ones it does not.

A 300-lead list is not a batch. `2026-08-02-q3` spent 182M tokens on 34 raw rows
and about 75% of that was the orchestrator's own context, so the size of a run
is a real decision and not a slicing convenience. This module makes that
decision once, deterministically, and writes it down.

## Why the cut is by evidence and not by row number

The naive split is thirds of the file. It is wrong here for a measurable reason:
the list's leads are not interchangeable. 33 of the 300 have an address the paid
verifier says is dead, and 76 have no LinkedIn, no Instagram and no website. A
dead address produces no row however good the hook is. A lead with no channel
has nowhere for research to look, so the activity floor cannot settle and no
hook can be cited — and the four agent passes spent finding that out are the
batch's actual bill, which is the same arithmetic `plan --addresses` exists for.

Thirds of the file would put a third of both groups in every chunk and pay for
them three times. So:

- **chunk-1 and chunk-2** are two stratified halves of the leads carrying a
  PASS-verified address **and** a LinkedIn URL. Same population, split on a
  seed, balanced on credential, emirate, and whether the lead also has a site or
  an Instagram. That is the point of halving rather than taking the first 62:
  **chunk 1's measured yield honestly predicts chunk 2's**, so the second chunk
  is a decision and not a hope.
- **chunk-3** is everyone else who could still receive an email and has
  somewhere to look — a WARN address, or a site or Instagram but no LinkedIn.
  A different population, and a separate question.
- **held-out** is the rest, each with a written reason.

## Held out is not dropped, and the file is why

`triage` learned this rule the hard way and `qualify` states it: a false kill is
permanent and invisible. Nothing here deletes a lead. Every excluded lead lands
in the held-out file carrying the reason it was excluded, so 120 missing rows
read as a decision somebody made rather than as an oversight — and so a later
source that supplies a channel makes them runnable again without re-deriving who
they were.

That file is the record, which is the same argument that puts
`data/contacted-before.csv` in the repo rather than in a CRM: membership is
cheap to store, read on every run, and expensive to reconstruct.

## The join

Leads join to the `icf-export` enriched CSV on `fetch.lead_key`, which for this
list is the lowercased email — every row has one and every one is unique. **A
lead the CSV does not carry is exit 1, named**, never silently held out: an
unjoined lead and an excluded lead look identical in the output and differ by
whether anybody decided anything.
"""
from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

from outbound.fetch import lead_key

CHUNK_1, CHUNK_2, CHUNK_3, HELD = "chunk-1", "chunk-2", "chunk-3", "held-out"
GROUPS = (CHUNK_1, CHUNK_2, CHUNK_3, HELD)

# The enriched CSV columns this reads. Owned by `icf_intake.ENRICHED_COLUMNS`
# and the source sheet; named here so a rename fails loudly at the assert below
# rather than quietly tiering every lead into held-out.
STATUS = "Email status"
LINKEDIN, INSTAGRAM = "LinkedIn URL", "Instagram URL"
SITE_LISTED, SITE_FOUND = "Website (listed)", "Website (found)"
DEDUPE = "Dedupe"
STRATA_COLUMNS = ("Credential", "Emirate")
REQUIRED = (STATUS, LINKEDIN, INSTAGRAM, SITE_LISTED, SITE_FOUND, DEDUPE,
            "Email") + STRATA_COLUMNS

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"

WALLED = ("already contacted — the wall caught this lead during enrichment, "
          "before a cent was spent")
DEAD = ("dead address — the paid verifier says nothing can be sent here, so "
        "no hook produces a row")
NO_CHANNEL = ("no channel of any kind — research has nowhere to look, so the "
              "activity floor cannot settle and no hook can be cited")

REASONS = {CHUNK_1: "PASS address and a LinkedIn URL",
           CHUNK_2: "PASS address and a LinkedIn URL",
           CHUNK_3: "reachable with somewhere to look, but not both"}


class ChunkError(Exception):
    """The list or the enrichment could not be read at all. Exit 2."""


# ------------------------------------------------------------------ the rules

def truthy(row: dict, column: str) -> bool:
    """One enriched cell, read as present or absent."""
    return bool((row.get(column) or "").strip())


def has_channel(row: dict) -> bool:
    """Anywhere a research worker could look. A site counts either way it came.

    The listed and the found website are two columns because provenance
    differs — `icf-export` writes the discovered one only when it is not a copy
    of what the sheet already carried, which is the defect the 2026-08-03 run
    found by reading output rather than counters. For "is there anywhere to
    look" they are the same fact.
    """
    return any(truthy(row, c) for c in
               (LINKEDIN, INSTAGRAM, SITE_LISTED, SITE_FOUND))


def tier(row: dict) -> tuple[str, str]:
    """Which pool this lead belongs to, and why. `strong` | `weak` | HELD.

    Order matters and it is cheapest-exclusion-first: the wall before the
    verifier before the channels. A lead that is both walled and unreachable is
    reported as walled, because that is the reason that would still hold if the
    address were fixed.
    """
    if (row.get(DEDUPE) or "").strip() != "clear":
        return HELD, WALLED
    status = (row.get(STATUS) or "").strip().upper()
    if status == FAIL:
        return HELD, DEAD
    if not has_channel(row):
        return HELD, NO_CHANNEL
    if status == PASS and truthy(row, LINKEDIN):
        return "strong", REASONS[CHUNK_1]
    return "weak", REASONS[CHUNK_3]


def strata(row: dict) -> tuple:
    """What the two halves are balanced on.

    Credential and emirate because they are the list's own segmentation, and
    the extra channels because a lead that also has a site or an Instagram has
    a second place to find a dated observation. Balancing on those is what stops
    one half being the easy one — which would make chunk 1's yield a number that
    predicts nothing, and prediction is the whole reason for halving.
    """
    return tuple((row.get(c) or "").strip() for c in STRATA_COLUMNS) + (
        truthy(row, SITE_LISTED) or truthy(row, SITE_FOUND),
        truthy(row, INSTAGRAM))


def halve(rows: list[dict], *, seed: int) -> tuple[list[dict], list[dict]]:
    """Two halves, balanced within every stratum and equal to within one.

    The alternation counter runs **across** strata rather than resetting inside
    each one. Resetting it is the obvious implementation and it is biased: every
    odd-sized stratum then hands its extra lead to the same half, and on the
    live list 124 leads came out 67/57. Carried, they come out 62/62.

    Sorted by key before shuffling so the seed is the only source of order —
    the same list produces the same two halves whatever order it arrived in.
    """
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for row in sorted(rows, key=lambda r: (r.get("Email") or "").lower()):
        buckets[strata(row)].append(row)

    rng = random.Random(seed)
    left: list[dict] = []
    right: list[dict] = []
    flip = 0
    for key in sorted(buckets, key=lambda k: tuple(str(x) for x in k)):
        group = buckets[key][:]
        rng.shuffle(group)
        for row in group:
            (left if flip % 2 == 0 else right).append(row)
            flip += 1
    return left, right


# ------------------------------------------------------------------- the join

def load_enriched(path) -> dict[str, dict]:
    """The enriched CSV keyed the way `fetch.lead_key` keys a Lead."""
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise ChunkError(f"could not read {path}: {exc}") from exc
    if not rows:
        raise ChunkError(f"{path} has no rows — an unreadable enrichment is "
                         f"not a list of zero coaches")
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        raise ChunkError(f"{path} is missing column(s): {', '.join(missing)}. "
                         f"It should be what `icf-export --csv` wrote.")
    return {(row.get("Email") or "").strip().lower(): row for row in rows
            if (row.get("Email") or "").strip()}


def assign(leads, enriched: dict[str, dict], *, seed: int) -> tuple[dict, dict, list]:
    """Every lead into exactly one group.

    Returns `(groups, reasons, unjoined)`. `groups` maps a group name to the
    Leads in it; `reasons` maps a lead key to why it landed there; `unjoined`
    is every lead the enrichment does not carry, which the caller must fail on
    rather than absorb.
    """
    by_key = {}
    unjoined = []
    for lead in leads:
        key = lead_key(lead)
        row = enriched.get(key)
        if row is None:
            unjoined.append(lead)
        else:
            by_key[key] = (lead, row)

    pools: dict[str, list] = {"strong": [], "weak": [], HELD: []}
    reasons: dict[str, str] = {}
    for key, (lead, row) in by_key.items():
        name, reason = tier(row)
        pools[name].append((lead, row))
        reasons[key] = reason

    left, right = halve([row for _, row in pools["strong"]], seed=seed)
    strong = {(r.get("Email") or "").strip().lower(): lead
              for lead, r in pools["strong"]}

    groups = {
        CHUNK_1: [strong[(r.get("Email") or "").strip().lower()] for r in left],
        CHUNK_2: [strong[(r.get("Email") or "").strip().lower()] for r in right],
        CHUNK_3: [lead for lead, _ in pools["weak"]],
        HELD: [lead for lead, _ in pools[HELD]],
    }
    return groups, reasons, unjoined


def held_records(leads, reasons: dict[str, str]) -> list[dict]:
    """The held-out file: who, and why, and nothing runnable.

    Deliberately not a leads file. A held-out lead is a decision, not an input,
    and a file that loads as leads is a file somebody eventually runs.
    """
    return [{"lead_key": lead_key(lead),
             "name": getattr(lead, "name", ""),
             "email": getattr(lead, "email", ""),
             "reason": reasons.get(lead_key(lead), "")}
            for lead in leads]


# ---------------------------------------------------------------- the reading

def composition(leads, enriched: dict[str, dict]) -> str:
    """One line of what a group is made of, for the two halves to be compared.

    This is the check on the halving and it is meant to be read rather than
    asserted: two halves that match on credential, emirate, site and Instagram
    are two halves whose yields are comparable.
    """
    rows = [enriched[k] for k in (lead_key(l) for l in leads) if k in enriched]
    creds = Counter((r.get("Credential") or "?").strip() for r in rows)
    return (f"{len(leads):3}  "
            + " ".join(f"{c} {creds[c]}" for c in ("MCC", "PCC", "ACC") if creds[c])
            + f"  Dubai {sum(1 for r in rows if (r.get('Emirate') or '').strip() == 'Dubai')}"
            + f"  site {sum(1 for r in rows if truthy(r, SITE_LISTED) or truthy(r, SITE_FOUND))}"
            + f"  ig {sum(1 for r in rows if truthy(r, INSTAGRAM))}")


def report(groups: dict, reasons: dict[str, str], enriched: dict[str, dict]) -> str:
    """The composition table, and the held-out reasons broken out."""
    total = sum(len(v) for v in groups.values())
    lines = [f"CHUNK: {total} lead(s) into {len(GROUPS)} group(s)"]
    for name in GROUPS:
        lines.append(f"  {name:9} {composition(groups[name], enriched)}")
    held = Counter(reasons.get(lead_key(l), "") for l in groups[HELD])
    for reason, count in held.most_common():
        lines.append(f"    held {count:3}  {reason}")
    return "\n".join(lines)


def write(groups: dict, reasons: dict[str, str], out_dir, *, prefix: str) -> list[str]:
    """Four files, and the paths they went to."""
    import json

    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name in (CHUNK_1, CHUNK_2, CHUNK_3):
        path = directory / f"{prefix}-{name}.json"
        path.write_text(
            json.dumps([l.to_dict() for l in groups[name]], indent=2, default=str),
            encoding="utf-8")
        written.append(str(path))
    path = directory / f"{prefix}-{HELD}.json"
    path.write_text(
        json.dumps(held_records(groups[HELD], reasons), indent=2, default=str),
        encoding="utf-8")
    written.append(str(path))
    return written
