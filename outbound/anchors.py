"""The anchor draw: which of Haytham's hand-written lines this lead gets.

The drafting model does not compose from nothing and it does not concatenate
finished sentences either. It gets an **anchor** — four lines written by hand,
drawn deterministically for this specific lead — and its job is to make them
read as one email. It may re-voice a line for the transition into or out of the
hook. It may not change what a line claims.

Two things this module owns:

**The draw.** Seeded on `sha256(email)`, never the builtin `hash()`, which is
salted per process and would make "reproducible" quietly false between runs.
Identity is matched on `coach_type` AND `sells_to` together, because the
reference group has to match: a coach selling into organisations needs proof
about organisations, one selling to individuals needs volume. Exact-match runs
70/30 against generic so a segment doesn't read as one repeated sentence.

**The fact table.** `copy/results.csv` holds the eight real client results, one
per segment. This is the authority on every number that may appear in an email.
`allowed_numbers()` turns a lead into the exact set of digits its copy is
permitted to contain, and `lint.py` rejects anything else. That check is what
makes it safe to let a model touch the identity beat at all: these numbers are
real, they will come up on a call, and these coaches compare emails.

The rule the fact table exists to enforce: **never relabel a result.** A
Leadership number may not be re-attributed to a Life coach to make the match
look tighter. Widening to "coaches here" is honest; relabelling is the tell that
the whole email was fabricated, hook included.
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass, field, fields as dataclass_fields
from pathlib import Path

COPY_DIR = Path(__file__).resolve().parent.parent / "copy"

EXACT_MATCH_RATIO = 0.70    # segment-matched line 70% of the time, generic 30%

# How far above the reference an authored identity sentence may run. The drafter
# writes that beat, so every length figure here is really a figure about this
# slack: `Deal.hook_room()` promises the room that survives the top of it, and
# `_resolve_length` repairs against the same number so the promise holds.
IDENTITY_SLACK = 3

# The loaded bank, cached for the life of the process. See CopyBank.load.
_BANK: "CopyBank | None" = None


def reset_cache() -> None:
    """Drop the cached bank. For tests, and for a re-read after copy-sync."""
    global _BANK
    _BANK = None


# --------------------------------------------------------------- the fact table


def period_numbers(text: str) -> set[int]:
    """"6 weeks" -> {6, 42}. "60 days" -> {60, 2}. Exact conversions only.

    A period is the one fact an honest line routinely restates in another unit,
    so both units have to be licensed. Approximations are not: 45 days is 6.4
    weeks, and rounding that to 6 would license a number nobody's data supports.
    """
    numbers: set[int] = set()
    for amount, unit in re.findall(r"(\d+)\s*(day|week|month|year)s?", text or "", re.I):
        value = int(amount)
        unit = unit.lower()
        numbers.add(value)
        if unit == "day":
            if value % 7 == 0:
                numbers.add(value // 7)
            if value % 30 == 0:
                numbers.add(value // 30)
        elif unit == "week":
            numbers.add(value * 7)
        elif unit == "month":
            numbers.add(value * 30)
    return numbers


@dataclass
class SegmentResult:
    """One real client result. Every field is a number an email may cite."""
    segment: str
    city: str
    sells_to: str
    client_price_aed: int
    meetings: int
    period: str
    first_meeting_days: int
    # When the first client SIGNED, as opposed to when the first meeting
    # happened. Blank on every row nobody measured it for, and blank is not a
    # zero — `claim_for` refuses a Claim that names a column this row has not
    # got, so an unmeasured segment cannot have a speed-to-client line at all.
    # Added 2026-08-01: two live lines said "landed their first client in week
    # 1" and the nearest column was `first_meeting_days`, which is a different
    # event. The lines were right and the table was short a column.
    first_client_days: int | None
    clients: int
    aed_closed: int
    close_period: str
    sourced: int
    sent: int
    still_working: bool

    def numbers(self) -> set[int]:
        """Every integer this result licenses.

        Periods expand into their exact equivalents, because "60 days" and
        "2 months" are the same fact stated two ways and a checker that only
        knows one of them would reject an honest line. Only exact conversions
        are licensed: 60 days is 2 months, 45 days is not 6 weeks.
        """
        found = {
            self.meetings, self.first_meeting_days, self.clients,
            self.aed_closed, self.client_price_aed,
            *( (self.first_client_days,) if self.first_client_days else () ),
            # The docstring says every field is citable, and these two were not
            # in the set: a line saying "I wrote to 401 business coaches" was
            # rejected as invented although 401 is this row's own `sent`.
            self.sourced, self.sent,
        }
        for text in (self.period, self.close_period):
            found |= period_numbers(text)
        return found


@dataclass
class FactTable:
    results: dict[str, SegmentResult] = field(default_factory=dict)

    @property
    def total_meetings(self) -> int:
        return sum(r.meetings for r in self.results.values())

    @property
    def total_clients(self) -> int:
        return sum(r.clients for r in self.results.values())

    @property
    def total_aed(self) -> int:
        return sum(r.aed_closed for r in self.results.values())

    @property
    def total_sent(self) -> int:
        return sum(r.sent for r in self.results.values())

    def aggregate_numbers(self) -> set[int]:
        """Numbers any lead may cite, because they are true of the whole book.

        Includes the rounded-down AED figure: the aggregate lines say 400,000
        against a real 416,000, and rounding down is the only direction that
        stays honest.
        """
        total_aed = self.total_aed
        rounded = (total_aed // 100_000) * 100_000
        numbers = {
            self.total_meetings, self.total_clients, total_aed, rounded,
            rounded // 1000, total_aed // 1000, self.total_sent,
            len(self.results),
        }
        if self.total_meetings:
            numbers.add(round(100 * self.total_clients / self.total_meetings))
        if self.total_sent:
            # A float, and the old `isinstance(n, int)` filter on the next line
            # threw it straight back out — so the real reply rate (3.2%) was
            # unwritable, while `lint._licensed` carried rounding logic that
            # existed only to accept it. A gate that cannot pass a true number
            # is a gate that teaches drafters to distrust it.
            numbers.add(round(100 * self.total_meetings / self.total_sent, 1))
        return {n for n in numbers if isinstance(n, (int, float))
                and not isinstance(n, bool)}


def load_facts(path: Path | None = None) -> FactTable:
    path = path or COPY_DIR / "results.csv"
    table = FactTable()
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            table.results[row["segment"]] = SegmentResult(
                segment=row["segment"],
                city=row["city"],
                sells_to=row["sells_to"],
                client_price_aed=int(row["client_price_aed"]),
                meetings=int(row["meetings"]),
                period=row["period"],
                first_meeting_days=int(row["first_meeting_days"]),
                first_client_days=(int(row["first_client_days"])
                                   if (row.get("first_client_days") or "").strip() else None),
                clients=int(row["clients"]),
                aed_closed=int(row["aed_closed"]),
                close_period=row["close_period"],
                sourced=int(row["sourced"]),
                sent=int(row["sent"]),
                still_working=row["still_working"].strip().lower() == "yes",
            )
    return table


# Numbers every email may carry because they describe the offer, not a client.
# "15 minutes", "10 names", "the other forty", "about a hundred coach sites,
# six published a price."
OFFER_NUMBERS = {10, 15, 40, 50, 100, 6, 1, 24}


# ------------------------------------------------------------------ the claim
#
# An identity line is the one beat the drafting model AUTHORS rather than
# reproduces. That is not a new licence, it is a description: `lint.check_bridge`
# requires a second-person clause before the first digit, and 21 of the live
# bank's 33 identity lines open on a bare stat, so two-thirds of leads already
# get a sentence the model wrote. The bank line is its register.
#
# What was never checked is what the authored sentence CLAIMS. `check_numbers`
# admits any figure true of any segment; `check_attribution` catches a number
# next to the wrong segment noun but only within one sentence and only for
# numbers. Between them a line could assert a real figure about the wrong
# result, a city that belongs to another row, or a retention that was never
# true — and one did: `id-fit-2` shipped "closed AED 36k in 6 weeks" against a
# Fitness row whose close_period is 45 days, passing only because 6 happens to
# be in OFFER_NUMBERS.
#
# So each identity line declares a Claim: which results.csv row, which of its
# columns, and whether it may name the segment at all. The line's words are
# free; its claim is not.

CLAIM_GRAMMAR = "<Segment>:<col>[,<col>...][|widened][+<qualifier>]  or  aggregate:<agg>[,<agg>...]"

# The column vocabulary is derived from the fact table rather than listed here,
# so a new results.csv column is citable the day it exists and a typo in a
# Claim is a parse error rather than a silently unchecked assertion.
CLAIM_COLUMNS = tuple(f.name for f in dataclass_fields(SegmentResult)
                      if f.name not in ("segment",))

# The aggregate vocabulary is the FactTable's own totals, for the lines that
# legitimately cite no single row ("67 meetings across 8 practices").
CLAIM_AGGREGATES = ("total_meetings", "total_clients", "total_aed", "total_sent",
                    "practices")

# A qualifier names a property of the meetings that a COLUMN backs. It exists
# so a line can say "every one with somebody who could sign off" and have that
# be checkable rather than a flourish: budget-holder and decision-maker both
# rest on the row's `sells_to = corporates`. Anything a column cannot back is
# not a qualifier, which is the whole point — "all with prospects ready to say
# yes" describes prospect intent, and nothing in this operation measures that.
CLAIM_QUALIFIERS = {
    "budget-holder": ("sells_to", "corporates"),
    "decision-maker": ("sells_to", "corporates"),
}


class ClaimError(ValueError):
    """A Claim that does not parse, or names something the fact table has not
    got. Raised rather than swallowed: a Claim nobody can read is a line whose
    figures are unchecked, which is the state this whole mechanism replaces."""


@dataclass
class ClaimSpec:
    """What an identity sentence must assert, and may not assert beyond.

    `figures` is the resolved column -> value map. `widened` means the line uses
    a real row's numbers WITHOUT naming its segment — legal, and the single most
    important thing this grammar has to express, because six live `Any`-typed
    lines do exactly that ("a coach here who closed 6 of the 9 meetings I set
    up" is Health's row with the label taken off).
    """
    segment: str = ""
    columns: tuple[str, ...] = ()
    widened: bool = False
    qualifier: str = ""
    figures: dict = field(default_factory=dict)
    city: str = ""
    raw: str = ""

    @property
    def aggregate(self) -> bool:
        return self.segment == "aggregate"

    @property
    def names_segment(self) -> bool:
        """May the sentence say "a business coach"? Only when the claim is
        scoped to a segment and not widened."""
        return bool(self.segment) and not self.aggregate and not self.widened

    def numbers(self) -> set:
        """Every value this claim licenses, and nothing else. Deliberately NOT
        unioned with OFFER_NUMBERS: the offer's ten names and fifteen minutes
        belong in the offer and close beats, and admitting them here is exactly
        what let a wrong 6 ride into a proof sentence."""
        licensed: set = set()
        for column, value in self.figures.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                licensed.add(value)
                if column in ("aed_closed", "client_price_aed", "total_aed") and value >= 1000:
                    licensed.add(value // 1000)
            elif isinstance(value, str):
                licensed |= period_numbers(value)
            if (column in ("first_meeting_days", "first_client_days")
                    and isinstance(value, int) and value > 0):
                # "inside a week" for 7 days, "in week 2" for 10. The ceiling is
                # exact under the "inside" framing rather than the rounding this
                # module refuses elsewhere: a first meeting on day 10 really did
                # happen inside week 2. Both columns, because `lint._renderings`
                # accepts the week form for both — and licensing a rendering the
                # figure check then rejects is a gate contradicting itself.
                licensed.add(-(-value // 7))
        return licensed


def parse_claim(raw: str) -> ClaimSpec:
    """`Business:meetings,period,clients+budget-holder` -> a ClaimSpec.

    Grammar only — this never touches the fact table, so it can be read and
    tested without one. `claim_for` resolves the figures.
    """
    text = (raw or "").strip()
    if not text:
        raise ClaimError(f"empty Claim. Expected {CLAIM_GRAMMAR}")

    body, _, qualifier = text.partition("+")
    qualifier = qualifier.strip()
    if qualifier and qualifier not in CLAIM_QUALIFIERS:
        raise ClaimError(
            f"qualifier {qualifier!r} is not backed by a column. "
            f"Known: {', '.join(sorted(CLAIM_QUALIFIERS))}")

    body, _, widened_flag = body.partition("|")
    widened_flag = widened_flag.strip()
    if widened_flag and widened_flag != "widened":
        raise ClaimError(f"{widened_flag!r} after | is not a modifier. Only 'widened' is.")

    segment, sep, columns_text = body.partition(":")
    segment = segment.strip()
    if not sep:
        raise ClaimError(f"no ':' in {text!r}. Expected {CLAIM_GRAMMAR}")

    columns = tuple(c.strip() for c in columns_text.split(",") if c.strip())
    if not columns:
        raise ClaimError(f"{text!r} names a row but no columns of it")

    allowed = CLAIM_AGGREGATES if segment == "aggregate" else CLAIM_COLUMNS
    unknown = [c for c in columns if c not in allowed]
    if unknown:
        raise ClaimError(
            f"{', '.join(unknown)} is not a column of {segment}. "
            f"Known: {', '.join(allowed)}")
    if segment == "aggregate" and widened_flag:
        raise ClaimError("an aggregate claim names no segment, so it cannot be widened")

    return ClaimSpec(segment=segment, columns=columns, widened=bool(widened_flag),
                     qualifier=qualifier, raw=text)


def claim_for(line: "Line", facts: FactTable) -> ClaimSpec | None:
    """The resolved claim behind one identity line, or None for a beat that has
    none. Raises ClaimError when the line declares a Claim the fact table cannot
    answer — a segment with no row, or a qualifier the row does not back."""
    raw = (line.meta or {}).get("claim", "")
    if not str(raw).strip():
        return None
    spec = parse_claim(str(raw))

    if spec.aggregate:
        totals = {
            "total_meetings": facts.total_meetings,
            "total_clients": facts.total_clients,
            "total_aed": (facts.total_aed // 100_000) * 100_000,
            "total_sent": facts.total_sent,
            "practices": len(facts.results),
        }
        spec.figures = {c: totals[c] for c in spec.columns}
        return spec

    result = facts.results.get(spec.segment)
    if result is None:
        raise ClaimError(
            f"{spec.segment} has no row in results.csv. "
            f"Known: {', '.join(sorted(facts.results))}")

    # A blank cell is "nobody measured this", not zero. Claiming it would be
    # inventing a result, which is the one thing the fact table exists to stop.
    unmeasured = [c for c in spec.columns
                  if getattr(result, c) is None or getattr(result, c) == ""]
    if unmeasured:
        raise ClaimError(
            f"{spec.segment} has no {', '.join(unmeasured)} recorded, so no line "
            f"may claim it. Measure it into copy/results.csv or drop it from the Claim.")

    spec.figures = {c: getattr(result, c) for c in spec.columns}
    spec.city = result.city

    if spec.qualifier:
        column, wanted = CLAIM_QUALIFIERS[spec.qualifier]
        actual = getattr(result, column)
        if str(actual).strip().lower() != wanted:
            raise ClaimError(
                f"{spec.qualifier} needs {spec.segment}.{column} == {wanted!r}, "
                f"but it is {actual!r}")
    return spec


# ------------------------------------------------------------------ the lines


@dataclass
class Line:
    id: str
    line: str
    meta: dict = field(default_factory=dict)


def _read_lines(name: str) -> list[Line]:
    """One beat's lines, sorted by id — the same canonical order every source
    produces, so a lead draws the same line whether the bank came from Airtable,
    a snapshot, or this file."""
    path = COPY_DIR / name
    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return sorted(
        (Line(id=row["id"], line=row["line"],
              meta={k: v for k, v in row.items() if k not in ("id", "line")})
         for row in rows),
        key=lambda line: line.id,
    )


@dataclass
class CopyBank:
    identity: list[Line]
    offer: list[Line]
    cta: list[Line]
    ps: list[Line]
    source: str = "csv"
    # Why this bank is not the live table, in a sentence someone can act on.
    # Empty when `source == "airtable"`. It exists because the fallbacks used to
    # be silent: a dead key, a network blip and a rejected edit all landed on the
    # committed CSVs with nothing printed anywhere, so a batch could be drafted
    # from month-old copy while the operator believed Airtable was in charge.
    reason: str = ""
    # Lint problems from a table that ANSWERED. This is the one fallback that is
    # drift rather than an outage: Airtable is reachable, somebody's edit is
    # live there, and it is not shippable. `deal` blocks on it.
    rejected: list[str] = field(default_factory=list)

    @property
    def is_live(self) -> bool:
        return self.source == "airtable"

    def status_line(self) -> str:
        """One line naming where the copy in this batch actually came from."""
        total = len(self.identity) + len(self.offer) + len(self.cta) + len(self.ps)
        if self.is_live:
            return f"COPY: airtable — {total} line(s) live from Copy Assets"
        return f"COPY: {self.source} — {total} line(s), NOT live: {self.reason}"

    @classmethod
    def from_lines(cls, lines: list[dict], source: str) -> "CopyBank":
        def beat(name: str) -> list[Line]:
            # Sorted by id: the draw indexes into this list, so the order has to
            # be a property of the data rather than of whichever source it came
            # from. See copy_sync.normalize_records.
            return sorted(
                (Line(id=l["id"], line=l["line"], meta=dict(l.get("meta", {})))
                 for l in lines if l.get("beat") == name),
                key=lambda line: line.id,
            )
        return cls(identity=beat("identity"), offer=beat("offer"),
                   cta=beat("cta"), ps=beat("ps"), source=source)

    @classmethod
    def from_csv(cls) -> "CopyBank":
        """The committed files, no network. Always available."""
        return cls(
            identity=_read_lines("identity.csv"),
            offer=_read_lines("offer.csv"),
            cta=_read_lines("cta.csv"),
            ps=_read_lines("ps.csv"),
            source="csv",
        )

    @classmethod
    def load(cls, *, refresh: bool = False) -> "CopyBank":
        """Airtable if reachable, the last synced snapshot if not, CSV if neither.

        **Airtable's Copy Assets table is the authority on every line.** The
        files under `copy/` are a cache of it, regenerated by `copy-sync` and
        committed so the machine still runs when Airtable does not. They are
        never the source of a line anybody chose; they are the last thing
        Airtable said. The order is the whole design:

        1. **Live Airtable**, whenever `AIRTABLE_API_KEY` is set — which it is
           in a Claude Code session, so this is the normal path, not a someday
           path.
        2. **`copy/_airtable.json`**, the snapshot written by
           `main.py copy-sync`. The fallback for a run with no key, which is
           what CI and the test suite are.
        3. **`copy/*.csv`**, committed and always present.

        Every path above the CSVs has already passed `copy_sync.validate`, so a
        line reaching a draft has been checked for invented numbers, relabelled
        segments, and weights that leave leads drawing nothing. A live fetch
        that fails validation falls through rather than shipping — better a
        slightly stale line than an unchecked one.

        **Every fall-through records why, on `reason`.** It used to swallow the
        exception and return the CSVs, which made the three interesting failures
        — a dead key, an unreachable base, and an edit that fails the lint —
        indistinguishable from the ordinary offline case and invisible in every
        one of them. `main.py copy-check` asserts rung 1; `deal` prints
        `status_line()` on every batch and blocks when `rejected` is non-empty.

        **Cached for the life of the process.** The lines do not change during a
        run, and `draw()` is called once per lead: without this, a 200-lead batch
        made 200 identical HTTP requests, spent minutes in pure latency, and
        would have tripped Airtable's 5-requests-per-second limit. Pass
        `refresh=True` after a `copy-sync` to pick up an edit mid-session.

        `OUTBOUND_COPY_SOURCE=csv` forces the offline path. The test suite sets
        it, so tests never touch the network and never depend on what someone
        typed into Airtable this morning.
        """
        global _BANK
        if _BANK is not None and not refresh:
            return _BANK

        import os
        from outbound import copy_sync

        forced = os.environ.get("OUTBOUND_COPY_SOURCE", "").strip().lower()
        rejected: list[str] = []

        if forced in ("csv", "snapshot"):
            reason = f"OUTBOUND_COPY_SOURCE={forced} pins the bank offline"
        else:
            reason = ""

        if forced != "csv":
            if forced != "snapshot":
                try:
                    from audit import airtable
                    if not airtable.available():
                        reason = ("no AIRTABLE_API_KEY in the environment, so "
                                  "the live table was never asked")
                    else:
                        records = airtable.copy_assets()
                        lines, _ = copy_sync.normalize_records(records)
                        if not lines:
                            # An authority that answers "nothing" must never
                            # read as "carry on with the old copy" — the same
                            # rule as an unreadable dedupe wall.
                            reason = ("Copy Assets returned no active lines — "
                                      "every row is unchecked or the table is "
                                      "empty")
                            rejected = [reason]
                        elif (problems := copy_sync.validate(lines)):
                            reason = (f"Airtable answered and {len(problems)} "
                                      f"problem(s) failed the lint, so the live "
                                      f"lines are not shippable")
                            rejected = problems
                        else:
                            _BANK = cls.from_lines(lines, "airtable")
                            return _BANK
                except Exception as exc:
                    # A dead key, a rename, a network blip. Never fatal: falling
                    # through to a checked snapshot beats stopping the run — but
                    # it is named now rather than swallowed.
                    reason = f"{type(exc).__name__}: {exc}"

            snapshot = copy_sync.load_snapshot()
            if snapshot:
                meta = copy_sync.snapshot_meta()
                synced = (meta or {}).get("synced_at") or "an unknown date"
                _BANK = cls.from_lines(snapshot, "snapshot")
                _BANK.reason = f"{reason}; using the snapshot synced {synced}"
                _BANK.rejected = rejected
                return _BANK

        _BANK = cls.from_csv()
        _BANK.reason = (f"{reason}; no snapshot either, so these are the "
                        f"committed CSVs" if reason else
                        "no snapshot, so these are the committed CSVs")
        _BANK.rejected = rejected
        return _BANK


# ------------------------------------------------------------------- the draw


def seed(email: str, salt: str = "") -> int:
    """Stable across processes and machines, unlike the builtin hash().

    The old assembler documented this and it matters more than it sounds: a
    salted hash makes every rebuild draw different lines, so "the same batch"
    is never the same batch and no A/B result means anything.
    """
    digest = hashlib.sha256(f"{(email or '').strip().lower()}|{salt}".encode()).hexdigest()
    return int(digest[:16], 16)


def _roll(email: str, salt: str, modulo: int = 100) -> int:
    """1..modulo, deterministic per lead per beat."""
    return (seed(email, salt) % modulo) + 1


def weight_of(line: Line) -> float:
    """A line's declared share. Blank means "equal share with its siblings".

    Weights replaced hand-maintained roll ranges. Under ranges, adding a fifth
    offer line meant renumbering all four existing ones so the spans stayed
    contiguous, by hand, with a validator that failed the whole sync if the
    arithmetic slipped. A weight is one number that cannot be wrong on its own.
    """
    raw = str(line.meta.get("weight", "") or "").strip()
    try:
        value = float(raw)
    except ValueError:
        return 0.0
    return max(0.0, value)


def shares(lines: list[Line]) -> dict[str, float]:
    """Each line's share of its beat, normalised to 1. Never a gap, never an
    overlap — those failure modes belonged to ranges and no longer exist."""
    if not lines:
        return {}
    weights = {line.id: weight_of(line) for line in lines}
    total = sum(weights.values())
    if total <= 0:
        equal = 1.0 / len(lines)
        return {line.id: equal for line in lines}
    return {line_id: w / total for line_id, w in weights.items()}


def draw_weighted(lines: list[Line], email: str, salt: str) -> Line:
    """One lead's line, by weight. The single-lead path.

    Cumulative shares rather than declared ranges, so the ranges are derived
    and always contiguous by construction. Deterministic per lead forever,
    which is what `outbound-draft` needs when there is no batch to balance
    against. For a batch, use `deal` — see why below.
    """
    if not lines:
        raise ValueError("no lines to draw from")
    roll = _roll(email, salt, 10_000) / 10_000
    cumulative = 0.0
    per_line = shares(lines)
    for line in lines:
        cumulative += per_line[line.id]
        if roll <= cumulative:
            return line
    return lines[-1]


def allocate(lines: list[Line], count: int,
             weights: dict[str, float] | None = None) -> dict[str, int]:
    """How many of `count` leads each line should get. Largest remainder.

    Independent per-lead hashing is unbiased in the limit and wrong in
    practice: measured over the real offer lines, a 50-lead batch gave one line
    8% against a declared 20% and pushed another to 38%, over the 35% batch
    cap. It only converged near n=200, and batches are not that big.

    Largest-remainder allocation hits the declared weights as exactly as whole
    leads allow, so the repetition cap is satisfied by construction instead of
    being warned about after the fact.
    """
    lines = _unique(lines)
    if not lines or count <= 0:
        return {line.id: 0 for line in lines}

    per_line = _normalise(weights, lines) if weights else shares(lines)
    exact = {line.id: per_line[line.id] * count for line in lines}
    floors = {line_id: int(value) for line_id, value in exact.items()}
    remaining = count - sum(floors.values())

    # Ties break on a hash of the line id, not the id itself. Alphabetical
    # tie-breaking is deterministic AND systematically biased: with 3 leads over
    # 9 equally-weighted identity lines every remainder ties, and sorting by id
    # handed all three seats to `id-any-1/2/3` — so small segment groups never
    # drew their matched line at all, which is the entire point of the pool.
    order = sorted(lines, key=lambda l: (-(exact[l.id] - floors[l.id]),
                                         seed(l.id, "tiebreak")))
    for line in order[:remaining]:
        floors[line.id] += 1
    return floors


def _normalise(weights: dict[str, float], lines: list[Line]) -> dict[str, float]:
    total = sum(max(0.0, weights.get(l.id, 0.0)) for l in lines)
    if total <= 0:
        equal = 1.0 / len(lines)
        return {l.id: equal for l in lines}
    return {l.id: max(0.0, weights.get(l.id, 0.0)) / total for l in lines}


def deal(lines: list[Line], emails: list[str], salt: str,
         weights: dict[str, float] | None = None) -> dict[str, Line]:
    """Assign a whole batch at once so the declared weights actually hold.

    Deterministic given the same batch: leads are ordered by their own hash,
    then handed out against the allocation. Re-running a batch reproduces it
    exactly.

    The trade-off, stated plainly: a lead's line depends on the batch it was in,
    where `draw_weighted` depends only on the lead. That is the right trade here
    because dedupe means a lead appears in exactly one batch, and because the
    thing being protected against is two coaches who compare notes seeing the
    same sentence — which is a property of the batch, not of a lead.
    """
    if not lines:
        raise ValueError("no lines to draw from")
    lines = _unique(lines)
    ordered = sorted(dict.fromkeys(emails), key=lambda e: seed(e, salt))
    quota = allocate(lines, len(ordered), weights)

    assignment: dict[str, Line] = {}
    index = 0
    for line in lines:
        for _ in range(quota[line.id]):
            assignment[ordered[index]] = line
            index += 1
    for email in ordered[index:]:          # rounding slack, never more than one
        assignment[email] = lines[-1]
    return assignment


def _identity_pools(lines: list[Line], coach_type: str,
                    sells_to: str) -> tuple[list[Line], list[Line]]:
    """(exact-match pool, generic pool) for this lead's segment and audience."""
    def pool(type_match, sells_match) -> list[Line]:
        return [l for l in lines
                if type_match(l.meta.get("coach_type", ""))
                and sells_match(l.meta.get("sells_to", ""))]

    exact_both = pool(lambda t: t == coach_type,
                      lambda s: bool(sells_to) and s == sells_to)
    exact_type = pool(lambda t: t == coach_type, lambda s: s in ("any", ""))

    # The generic pool respects `sells_to` too. It used to take every `Any`
    # line regardless, which put corporate proof in front of coaches who sell to
    # individuals: "I get coaches in front of the people who actually hold the
    # budget" landed on a health coach whose buyer is one person paying for
    # themselves. A cold reader caught the mirror of it — an individuals-
    # flavoured generic reaching a corporate seller — and said the number "lands
    # on a market they do not sell into". Both directions are the same bug.
    #
    # A line tagged for an audience is only generic WITHIN that audience.
    # Audience-neutral lines (`any`) stay available to everyone, and a lead
    # whose own `sells_to` is unknown draws only from those — which is right,
    # since guessing the reference group is exactly what this avoids.
    generic = pool(
        lambda t: t == "Any",
        lambda s: s in ("any", "") or (bool(sells_to) and s == sells_to),
    )

    # Deduped. A line tagged `sells_to = any` satisfies BOTH exact_both (when
    # the lead's own sells_to is "any") and exact_type, so concatenating put it
    # in the pool twice — which silently double-weighted it in the per-lead
    # draw, and made the batch deal hand out more seats than there were leads.
    return _unique(exact_both + exact_type), generic


def _unique(lines: list[Line]) -> list[Line]:
    """First occurrence of each id, order preserved."""
    seen: set[str] = set()
    out = []
    for line in lines:
        if line.id not in seen:
            seen.add(line.id)
            out.append(line)
    return out


def _identity_pool(lines: list[Line], coach_type: str,
                   sells_to: str) -> tuple[list[Line], dict[str, float]]:
    """The eligible lines for this lead, and the weight each should carry.

    The 70/30 exact-to-generic ratio is expressed as weights rather than as a
    coin flip per lead. That makes it real at batch level — 7 of 10 Health leads
    genuinely get a Health line — instead of a per-lead gamble that clusters,
    and it is what stops equal weights from tying and handing every seat to
    whichever line sorts first.
    """
    exact, generic = _identity_pools(lines, coach_type, sells_to)
    if not exact and not generic:
        return lines, {}
    if not exact:
        return generic, {}
    if not generic:
        return exact, {}

    weights = {l.id: EXACT_MATCH_RATIO / len(exact) for l in exact}
    weights.update({l.id: (1 - EXACT_MATCH_RATIO) / len(generic) for l in generic})
    return exact + generic, weights


def draw_identity(lines: list[Line], email: str, *,
                  coach_type: str, sells_to: str) -> Line:
    """Match on segment AND audience, with a 70/30 exact-to-generic split.

    Falls through in order: exact segment + exact audience -> exact segment,
    any audience -> generic (`Any`). An unknown `sells_to` never invents a
    match; it just drops to the segment-only pool, which is honest.
    """
    exact, generic = _identity_pools(lines, coach_type, sells_to)
    if exact and generic:
        # 70/30, decided per lead so the ratio holds across a batch without
        # anyone tracking a running count.
        use_exact = _roll(email, "identity-mix", 100) <= EXACT_MATCH_RATIO * 100
        pool_choice = exact if use_exact else generic
    else:
        pool_choice = exact or generic or lines

    return pool_choice[seed(email, "identity") % len(pool_choice)]


@dataclass
class Anchor:
    """The four hand-written lines this lead drew, plus what it may cite."""
    identity: Line
    offer: Line
    cta: Line
    ps: Line
    segment: str = ""
    allowed_numbers: set = field(default_factory=set)
    # True when the deal had to move a beat to leave room for the hook. Carried
    # so `deal` can report the weight drift it caused rather than absorb it.
    length_repaired: bool = False
    # What the identity sentence must assert. None only when the line carries no
    # Claim, which `copy-sync` refuses — so in practice this is always set, and
    # the drafter's prompt says so rather than quietly dropping the constraint.
    claim: "ClaimSpec | None" = None

    def authored_budget(self) -> int:
        """Words the hook and the identity beat have BETWEEN them.

        This is the only length figure here that is true at deal time, because
        it depends on nothing the drafter has yet written: the ceiling, less the
        three hand-written lines, the greeting and the sign-off.

        **Subtracting a separately-counted identity sentence from it gets close
        and not exact**, and that is not a bug to iron out. `lint.word_count`
        runs on the assembled body, which is why `lint.hook_room` measures the
        body rather than summing lines — the joins are worth a word or two
        either way. On `2026-08-02-q2` one shipped email came out a word over
        its derived budget and still landed at 94 of 95.

        So this is a guide and `WORD_MAX` is the enforcement. `hook_room()`
        below is deliberately conservative enough to absorb the difference.
        """
        from outbound.lint import hook_room

        return hook_room({"identity": "", "offer": self.offer.line,
                          "cta": self.cta.line, "ps": self.ps.line})

    def hook_room(self) -> int:
        """Words this lead's hook is GUARANTEED, whatever the drafter writes.

        Measured against the top of `identity_budget()` rather than against the
        reference identity line. The difference matters because the drafter
        authors that sentence: a number computed on the reference is the room a
        hook has only if the identity beat comes out exactly reference length,
        and drafters write to the top of a range far more often than to its
        middle.

        `2026-08-02-q2` is the evidence. Every lead in it wrote at or above the
        reference, so every printed figure overstated the room, and three
        different drafters independently recomputed it and told the
        orchestrator the instruction was wrong. They were right every time:
        Sabine was told 18 and had 16, John was told 32 and had 22. The cost
        was rounds — a drafter trims to a number, is told the real one, and
        trims again — and the orchestrator relaying it got it wrong twice more
        even after being corrected.

        So this returns the floor. A hook that fits in fewer is better anyway,
        and a drafter who writes a short identity beat finds room it did not
        expect, which is the harmless direction to be wrong in.

        `authored_budget()` is the exact figure and the prompt hands over both.
        """
        return self.authored_budget() - self.identity_budget()[1]

    def identity_budget(self) -> tuple[int, int]:
        """The word range an authored identity sentence has to land in, so
        `hook_room` above stays honest. Three words either side of the
        reference: enough to re-shape a sentence, not enough to move the
        ceiling."""
        words = len(self.identity.line.split())
        return max(1, words - IDENTITY_SLACK), words + IDENTITY_SLACK

    def _identity_prompt_lines(self) -> list[str]:
        """The identity beat, as three things rather than one.

        A sentence to copy would be the old contract, and the old contract is
        what killed two send-ready leads: the defect was in the line, the
        drafter was not allowed to touch it, and the lead spent its one rewrite
        pass on a problem it could not fix. So the CLAIM is the constraint, the
        REFERENCE is the register, and the words are the drafter's.
        """
        low, high = self.identity_budget()
        out = [f"  identity [{self.identity.id}] — WRITE THIS SENTENCE YOURSELF.",
               f"    REFERENCE (Haytham's register, not text to reproduce):",
               f"      {self.identity.line}"]
        if self.claim is None:
            out.append("    CLAIM: none declared — do not add a figure this beat "
                       "does not already carry.")
        else:
            out.append("    CLAIM — every one of these must survive, in your words:")
            for column, value in self.claim.figures.items():
                out.append(f"      {column} = {value}")
            if self.claim.names_segment:
                out.append(f"      say it about a {self.claim.segment.lower()} coach")
            else:
                out.append("      do NOT name a segment — these figures are real "
                           "but the label is not yours to use here")
            if self.claim.qualifier:
                out.append(f"      the meetings were with a {self.claim.qualifier}")
            out.append("    NO OTHER FIGURE may appear in this beat. Licensed here: "
                       + (", ".join(str(n) for n in sorted(self.claim.numbers())) or "none"))
        out.append(f"    LENGTH: {low}-{high} words. The hook budget below was "
                   "measured against the reference.")
        avoid = self._seam_words()
        if avoid:
            # The cheap half of the seam fix. Dodging five words while writing
            # costs nothing; discovering the collision after the fact used to
            # cost a lead its only rewrite pass, because neither line was at
            # fault and the drafter could not touch either of them.
            out.append("    DO NOT REUSE (the offer beat below already says "
                       "these): " + ", ".join(avoid))
        return out

    def _seam_words(self, limit: int = 6) -> list[str]:
        """Words from the offer line the identity sentence should avoid.

        The offer line is drawn and cannot move; the identity sentence is
        written. So the repair belongs to whichever of the two is free, which is
        why this is a prompt line rather than a constraint on the deal.
        """
        from outbound.lint import _seam_words

        return sorted(_seam_words(self.offer.line))[:limit]

    def as_prompt_block(self) -> str:
        """What the drafting model actually sees."""
        return "\n".join([
            "ANCHOR LINES (hand-written by Haytham). Three of these four are his",
            "sentences: re-voice for flow, never change what they claim. The",
            "identity beat is different and is spelled out below.",
            "",
            *self._identity_prompt_lines(),
            "",
            f"  offer    [{self.offer.id}]: {self.offer.line}",
            f"  cta      [{self.cta.id}]: {self.cta.line}",
            f"  ps       [{self.ps.id}]: {self.ps.line}",
            "",
            f"WORD BUDGET. The hook and the identity beat share "
            f"{self.authored_budget()} words between",
            "them. That figure is exact: it is the 95-word ceiling less the "
            "three lines above,",
            "the greeting and the sign-off, none of which you write.",
            "",
            f"  HOOK ROOM: {self.hook_room()} words, guaranteed. That is the "
            "budget less the top of",
            f"  the identity range above, so it holds however long you write "
            "that sentence.",
            f"  Write a shorter identity beat and the hook has more: the exact "
            "figure is",
            f"  {self.authored_budget()} minus whatever your identity sentence "
            "comes out at.",
            "",
            "Neither is a target. A hook that fits in fewer is better, and the "
            "95-word",
            "ceiling is enforced — going over gets the email refused for length.",
        ])


def allowed_numbers(facts: FactTable, segment: str) -> set[int]:
    """The numbers a sentence may cite while naming this segment.

    Used for the attribution check: "a health coach closed AED 120,000" is a
    relabelled Business result and must fail, even though 120,000 is real.
    """
    numbers = set(OFFER_NUMBERS) | facts.aggregate_numbers()
    result = facts.results.get(segment)
    if result:
        numbers |= result.numbers()
    return numbers


def all_numbers(facts: FactTable) -> set[int]:
    """Every number that is true of some real client result.

    This is what a *widened* line may cite. The rules sanction three honest
    ways to vary an identity beat, and widening is one of them: drop the
    segment, keep "coaches here in the UAE", which is true of every lead.
    `id-corp-1` does exactly that with a Business result, and a checker scoped
    to the lead's own segment would wrongly reject it.

    Widening is legal because it makes no claim about which kind of coach.
    Relabelling — the same numbers with a *different* segment named next to
    them — is caught by the attribution check in `lint.py`, not here.
    """
    numbers = set(OFFER_NUMBERS) | facts.aggregate_numbers()
    for result in facts.results.values():
        numbers |= result.numbers()
    return numbers


def draw(email: str, *, coach_type: str = "", sells_to: str = "",
         bank: CopyBank | None = None, facts: FactTable | None = None) -> Anchor:
    """The whole draw for one lead. Deterministic given the same address.

    Runs the same length repair the batch deal does. A per-lead hash is just as
    capable of landing on a combination with no room for a hook — likelier, in
    fact, since it has no batch to spread against — and `outbound-draft` is
    exactly where nobody would think to look for the cause.
    """
    bank = bank or CopyBank.load()
    facts = facts or load_facts()
    identity = draw_identity(bank.identity, email,
                             coach_type=coach_type, sells_to=sells_to)
    drawn_segment = identity.meta.get("coach_type", "")
    segment = coach_type if drawn_segment == coach_type else ""

    fixed = {"offer": {email: draw_weighted(bank.offer, email, "offer")},
             "cta": {email: draw_weighted(bank.cta, email, "cta")},
             "ps": {email: draw_weighted(bank.ps, email, "ps")}}
    repaired = _resolve_length(fixed, {email: identity}, [email], bank)

    return Anchor(
        identity=identity,
        offer=fixed["offer"][email],
        cta=fixed["cta"][email],
        ps=fixed["ps"][email],
        segment=segment,
        allowed_numbers=all_numbers(facts),
        length_repaired=bool(repaired),
        claim=claim_for(identity, facts),
    )


def split_identity(lines: list[Line], emails: list[str], *,
                   coach_type: str, sells_to: str,
                   cap: float = 0.35) -> tuple[dict[str, Line], list[str]]:
    """Decide this segment's matched lines, and hand back who needs a generic one.

    Two stages, and the order matters. First decide *how many* of this group get
    a segment-matched line — 70/30 — then spread that many across the matched
    lines available. Doing it in one stage with per-line weights undershot to
    60%: Health has 3 matched lines against 6 generic ones, so the generic side
    carried the larger rounding remainders and took every leftover seat.

    The leads that did not get a matched line are RETURNED rather than dealt
    here, because the generic pool is shared by every segment in the batch and
    the repetition cap is a property of the batch, not of one group. Dealing
    generics per group put `id-any-1` in front of 42% of a 12-lead batch: six
    small groups each independently picked the same first line.
    """
    exact, generic = _identity_pools(lines, coach_type, sells_to)
    ordered = sorted(dict.fromkeys(emails), key=lambda e: seed(e, "identity-mix"))

    if not exact:
        return {}, ordered
    if not generic:
        return deal(exact, ordered, "identity"), []

    total = len(ordered)
    want_exact = int(total * EXACT_MATCH_RATIO)
    if (total * EXACT_MATCH_RATIO - want_exact) >= 0.5:
        want_exact += 1

    # The cap outranks the ratio. Executive has exactly one identity line usable
    # for an individuals-facing lead, so a straight 70% put that one sentence in
    # front of 70% of the batch. A weaker match beats the same sentence twice in
    # one inbox pair, so the excess spills to generic.
    ceiling = max(1, int(cap * total)) * len(exact)
    want_exact = min(want_exact, ceiling)

    return deal(exact, ordered[:want_exact], "identity"), ordered[want_exact:]


def thin_segments(bank: "CopyBank", *, cap: float = 0.35) -> dict[str, int]:
    """Segments with too few identity lines to fill their share without repeating.

    Reported rather than silently worked around: the spill above keeps a batch
    legal, but the real fix is writing another line for that segment, and nobody
    knows to do that unless something says so.
    """
    needed = {}
    for coach_type in {l.meta.get("coach_type", "") for l in bank.identity}:
        if not coach_type or coach_type == "Any":
            continue
        for sells_to in ("individuals", "corporates"):
            exact, _ = _identity_pools(bank.identity, coach_type, sells_to)
            if exact and len(exact) * cap < EXACT_MATCH_RATIO:
                shortfall = -(-int(EXACT_MATCH_RATIO * 100) // int(cap * 100)) - len(exact)
                if shortfall > 0:
                    needed[f"{coach_type}/{sells_to}"] = shortfall
    return needed


def deal_batch(leads: list[dict], *, bank: "CopyBank | None" = None,
               facts: FactTable | None = None) -> dict[str, Anchor]:
    """Anchors for a whole batch, allocated so the declared weights hold.

    `leads` is a list of dicts carrying at least `email`, and optionally
    `coach_type` and `sells_to`. Returns email -> Anchor.

    This is what `outbound-batch` uses. `draw()` stays the single-lead path for
    `outbound-draft`, where there is no batch to balance against. The two differ
    on purpose: per-lead hashing is unbiased only in the limit, and at 50 leads
    it missed a declared 20% weight by 12 points and broke the repetition cap.

    Identity is dealt per segment pool rather than globally, because the pool a
    lead draws from depends on its own `coach_type` and `sells_to` — balancing
    across leads that could never draw the same line would mean nothing.
    """
    bank = bank or CopyBank.load()
    facts = facts or load_facts()

    # Email is the identity key throughout this function, so a blank one merges
    # people. `Research.email` defaults to "", and two address-less leads
    # collapsed into a single anchor: three leads in, two out, with a Health
    # coach left holding a Business identity line and `deal` cheerfully
    # reporting "2 leads". Refused rather than worked around — a lead with no
    # address cannot be exported anyway, so silently dropping it here would only
    # move the confusion downstream.
    missing = [l for l in leads if not (l.get("email") or "").strip()]
    if missing:
        raise ValueError(
            f"{len(missing)} lead(s) have no email, and the deal is keyed by "
            f"address: {[l.get('name') or l.get('slug') or '?' for l in missing][:5]}. "
            f"Resolve or drop them before dealing.")
    seen: dict[str, int] = {}
    for lead in leads:
        seen[lead["email"]] = seen.get(lead["email"], 0) + 1
    duplicated = [e for e, n in seen.items() if n > 1]
    if duplicated:
        raise ValueError(
            f"the same address appears more than once in this batch: "
            f"{duplicated[:5]}. Dedupe before dealing, or one of them silently "
            f"takes the other's lines.")

    fixed: dict[str, dict[str, Line]] = {}
    for beat, lines in (("offer", bank.offer), ("cta", bank.cta), ("ps", bank.ps)):
        fixed[beat] = deal(lines, [l["email"] for l in leads], beat)

    # Identity: group leads by the pool they are eligible for, deal within each.
    pools: dict[tuple, list[dict]] = {}
    for lead in leads:
        key = (lead.get("coach_type", ""), lead.get("sells_to", ""))
        pools.setdefault(key, []).append(lead)

    identity: dict[str, Line] = {}
    segments: dict[str, str] = {}
    needs_generic: list[str] = []

    # Matched lines per segment; everyone else collected for one shared deal.
    for (coach_type, sells_to), group in pools.items():
        matched, spilled = split_identity(
            bank.identity, [l["email"] for l in group],
            coach_type=coach_type, sells_to=sells_to)
        identity.update(matched)
        needs_generic.extend(spilled)

    if needs_generic:
        _, generic = _identity_pools(bank.identity, "", "")
        identity.update(deal(generic or bank.identity, needs_generic,
                             "identity-generic"))

    for lead in leads:
        drawn = identity[lead["email"]].meta.get("coach_type", "")
        coach_type = lead.get("coach_type", "")
        segments[lead["email"]] = coach_type if drawn == coach_type else ""

    _resolve_echoes(fixed, [l["email"] for l in leads], bank)
    # After the echo pass, so a length swap cannot reintroduce a collision the
    # echo pass just cleared.
    repaired = _resolve_length(fixed, identity, [l["email"] for l in leads], bank)

    widened = all_numbers(facts)
    # Resolved once per LINE rather than once per lead. A 200-lead batch draws
    # from 33 identity lines, and re-resolving the same claim two hundred times
    # is the same shape of waste the copy-bank cache was added to stop.
    claims = {line.id: claim_for(line, facts) for line in bank.identity}
    return {
        lead["email"]: Anchor(
            identity=identity[lead["email"]],
            offer=fixed["offer"][lead["email"]],
            cta=fixed["cta"][lead["email"]],
            ps=fixed["ps"][lead["email"]],
            segment=segments[lead["email"]],
            allowed_numbers=widened,
            length_repaired=lead["email"] in repaired,
            claim=claims.get(identity[lead["email"]].id),
        )
        for lead in leads
    }


def rebalance_ps(drafted: list[dict], *, bank: "CopyBank | None" = None,
                 cap: float = 0.35) -> dict[str, str]:
    """Reallocate ONLY the ps across a set that has already been drafted.

    Holds are guaranteed by design — a refuted hook, a twice-refused draft — and
    every hold unbalances a deal that was made for the larger batch. On the first
    real run, dropping 3 of 11 put two ps lines at 38% against a 35% cap and the
    batch check blocked the whole file, correctly. Re-dealing from scratch is the
    wrong answer: it moves identity lines too, which means re-drafting emails
    that already passed a cold read.

    The ps is the one beat that can move safely. It is library copy the drafter
    is told to reproduce "verbatim or near", it sits alone at the end, and it
    takes no part in the seam between the hook and the identity beat — so
    swapping it is an allocation decision, not a drafting one. Identity, offer
    and cta stay exactly as written and verified.

    `drafted` is a list of dicts carrying `email` and `beats`. Returns
    email -> ps line id. Deterministic for a given set.
    """
    from outbound.lint import check_echo

    bank = bank or CopyBank.load()
    emails = sorted({d["email"] for d in drafted})
    if not emails:
        return {}
    beats_of = {d["email"]: d.get("beats", {}) for d in drafted}

    ceiling = max(1, int(cap * len(emails)))
    counts: dict[str, int] = {l.id: 0 for l in bank.ps}
    chosen: dict[str, str] = {}

    from outbound.lint import WORD_MAX, word_count

    def fits(beats: dict, line: str) -> bool:
        """The swap must not push the email over the word ceiling.

        A ps is 11 to 26 words, so exchanging one for another moves the total by
        up to 15 — enough to tip an email that was sitting at the cap. Two did,
        and were rejected for length by a change nobody wrote.

        Counted with `lint.word_count`, not `str.split()`. This ran on a real
        drafted body, where a separated figure is likeliest to appear, and
        `split()` scores "AED 91,500" one word lighter than the check that
        decides whether the email ships.
        """
        from outbound.export import assemble_body
        body = assemble_body({**beats, "ps": line}, greeting_name="Name")
        return word_count(body) <= WORD_MAX

    # Most-constrained first. Processing in address order let unconstrained
    # leads take the scarce lines, so the leads that could only accept two of
    # the four arrived to find nothing legal left — and the allocator reported
    # "no legal line" when a perfect 2/2/2/2 assignment existed. Ordering by how
    # few options a lead has is the standard fix and stays deterministic; the
    # address hash breaks ties.
    options = {e: [l for l in bank.ps
                   if fits(beats_of.get(e, {}), l.line)
                   and not check_echo({"offer": beats_of.get(e, {}).get("offer", ""),
                                       "cta": beats_of.get(e, {}).get("cta", ""),
                                       "ps": l.line})]
               for e in emails}
    emails = sorted(emails, key=lambda e: (len(options[e]), seed(e, "ps-order")))

    for email in emails:
        beats = beats_of.get(email, {})
        legal = [
            l for l in bank.ps
            if counts[l.id] < ceiling
            and fits(beats, l.line)
            and not check_echo({"offer": beats.get("offer", ""),
                                "cta": beats.get("cta", ""), "ps": l.line})
        ]
        # Word budget before share cap: a repeated sentence is a batch-quality
        # problem, an over-length email is refused outright.
        if not legal:
            legal = [l for l in bank.ps
                     if fits(beats, l.line)
                     and not check_echo({"offer": beats.get("offer", ""),
                                         "cta": beats.get("cta", ""), "ps": l.line})]
        # No legal line means the cap and the echo rule cannot both hold. Fall
        # back to echo-only: a repeated sentence is a batch-quality problem, a
        # contradictory one is an email nobody can fix.
        if not legal:
            legal = [l for l in bank.ps
                     if not check_echo({"offer": beats.get("offer", ""),
                                        "cta": beats.get("cta", ""), "ps": l.line})]
        if not legal:
            continue
        pick = min(legal, key=lambda l: (counts[l.id], seed(email, l.id)))
        counts[pick.id] += 1
        chosen[email] = pick.id
    return chosen


def echo_pairs(bank: "CopyBank") -> list[tuple[str, str]]:
    """Offer/ps line pairs that can never be dealt together.

    Reported by `deal` rather than merely worked around, because the workaround
    has a visible cost: a ps line that collides with one of four offers loses
    roughly a quarter of its allocation and can never reach its declared weight.
    Someone tuning weights needs to know that before concluding the allocator is
    broken.
    """
    from outbound.lint import check_echo

    out = []
    for offer in bank.offer:
        for ps in bank.ps:
            if check_echo({"offer": offer.line, "cta": "", "ps": ps.line}):
                out.append((offer.id, ps.id))
    return out


def _resolve_echoes(fixed: dict[str, dict[str, Line]], emails: list[str],
                    bank: "CopyBank") -> None:
    """Swap the ps when the dealt offer/cta/ps repeat a distinctive phrase.

    `b4-01` ("Not a scraped list") and `ps-01` ("not a list") are each fine and
    collide when dealt together: the same denial twice in ninety words reads as
    protesting too much. On the live bank that pair is 1 of 16, which is 124 of
    the 1,984 possible combinations, so roughly one email in sixteen was being
    rejected at export for something no drafter caused and none could fix
    without abandoning an anchor.

    Catching it at allocation is the same principle as `_check_hook_room`: a
    combination the linter will reject is a combination the deal should never
    have issued. The ps moves rather than the offer because ps is the shortest
    beat and the one the design already calls "verbatim or near", so replacing
    it costs the least. Weights drift by at most the number of swapped leads,
    which is far cheaper than losing those leads at the gate.

    Silent by design when a swap is available and impossible to miss when it is
    not: with no clean ps in the bank the pair is left alone and the linter
    still catches it downstream, which is the fail-closed direction.
    """
    from outbound.lint import check_echo

    # Replacements go to the currently least-used clean line, which keeps the
    # displaced share spread instead of piling it on one sentence. Taking the
    # first clean candidate pushed a ps line to 35% at n=200 — exactly the
    # repetition cap — and hashing instead put it at 36% on an 11-lead batch,
    # because a hash cannot see what it has already handed out. Counting can.
    # Ties break on the lead's own hash, and the whole pass runs in sorted email
    # order, so the result is still reproducible for a given batch.
    counts: dict[str, int] = {}
    for line in fixed["ps"].values():
        counts[line.id] = counts.get(line.id, 0) + 1

    for email in sorted(emails):
        offer = fixed["offer"].get(email)
        cta = fixed["cta"].get(email)
        ps = fixed["ps"].get(email)
        if not (offer and cta and ps):
            continue
        beats = {"offer": offer.line, "cta": cta.line, "ps": ps.line}
        if not check_echo(beats):
            continue
        clean = [c for c in bank.ps
                 if c.id != ps.id and not check_echo({**beats, "ps": c.line})]
        if not clean:
            continue                      # linter still catches it: fail closed
        pick = min(clean, key=lambda c: (counts.get(c.id, 0), seed(email, c.id)))
        counts[ps.id] -= 1
        counts[pick.id] = counts.get(pick.id, 0) + 1
        fixed["ps"][email] = pick


def _resolve_length(fixed: dict[str, dict[str, Line]], identity: dict[str, Line],
                    emails: list[str], bank: "CopyBank") -> set[str]:
    """Swap a beat when the dealt combination leaves no room for a hook.

    The hook is the only beat written per lead, so it is the only one that pays
    when the four drawn lines run long. The old defence was to require that the
    longest line in every beat could coexist, which made a length problem into a
    copy problem: the fix on offer was to trim a sentence somebody wrote by hand
    until it fit, for a combination no lead had to be given.

    This is the other end of it, and it is the rule `_resolve_echoes` already
    follows: **a combination the linter will reject is a combination the deal
    should never have issued.** The lines stay exactly as written. They just do
    not go out together.

    Order of what moves, cheapest first:

    - **ps.** Shortest beat, told to the drafter as "verbatim or near", takes no
      part in the seam between the hook and the identity beat. On the live bank
      this is always enough: the heaviest identity, offer and cta together leave
      13 words once the shortest ps is in place.
    - **cta, with the ps.** Both beats have four lines and a 10-word spread. Only
      reached if no ps alone gets there.
    - **Never identity, and never offer.** Identity is drawn from a pool matched
      to the lead's segment, and moving it trades the thing the 70/30 ratio
      exists to buy for words. Offer carries the beat the whole email is for.

    Swaps still have to satisfy the echo rule, so this cannot repair length by
    reintroducing the collision `_resolve_echoes` just cleared. Runs after it,
    for that reason.

    Returns the emails whose beats moved. Silent when a swap is available and
    reported by `deal` when it is not: a lead left short is not corrected here,
    it is handed to the linter, which refuses the email. Fail-closed.
    """
    from outbound.lint import check_echo, hook_room, MIN_HOOK_WORDS

    # The floor `Deal.hook_room()` promises, not the reference-length estimate.
    # The drafter authors the identity beat and may write to the top of its
    # range, so a combination that leaves MIN_HOOK_WORDS only when that sentence
    # comes out exactly reference length is a combination the linter can still
    # refuse. Repairing against the promise is what makes the promise true.
    floor = MIN_HOOK_WORDS + IDENTITY_SLACK

    counts: dict[str, dict[str, int]] = {}
    for beat in ("cta", "ps"):
        counts[beat] = {}
        for line in fixed[beat].values():
            counts[beat][line.id] = counts[beat].get(line.id, 0) + 1

    repaired: set[str] = set()

    for email in sorted(emails):
        drawn = identity.get(email)
        offer, cta, ps = (fixed["offer"].get(email), fixed["cta"].get(email),
                          fixed["ps"].get(email))
        if not (drawn and offer and cta and ps):
            continue
        beats = {"identity": drawn.line, "offer": offer.line,
                 "cta": cta.line, "ps": ps.line}
        if hook_room(beats) >= floor:
            continue

        def legal(trial: dict) -> bool:
            return (not check_echo(trial)
                    and hook_room(trial) >= floor)

        # Least-used replacement first, so the displaced share stays spread
        # instead of piling onto whichever line happens to be shortest. Ties
        # break on the lead's own hash, and the pass runs in sorted email
        # order, so a given batch always deals the same way.
        moved = False
        candidates = [c for c in bank.ps
                      if c.id != ps.id and legal({**beats, "ps": c.line})]
        if candidates:
            pick = min(candidates,
                       key=lambda c: (counts["ps"].get(c.id, 0), seed(email, c.id)))
            counts["ps"][ps.id] = counts["ps"].get(ps.id, 1) - 1
            counts["ps"][pick.id] = counts["ps"].get(pick.id, 0) + 1
            fixed["ps"][email] = pick
            moved = True
        else:
            pairs = [(c, p) for c in bank.cta for p in bank.ps
                     if legal({**beats, "cta": c.line, "ps": p.line})]
            if pairs:
                pick_cta, pick_ps = min(
                    pairs, key=lambda cp: (counts["cta"].get(cp[0].id, 0),
                                           counts["ps"].get(cp[1].id, 0),
                                           seed(email, cp[0].id + cp[1].id)))
                counts["cta"][cta.id] = counts["cta"].get(cta.id, 1) - 1
                counts["cta"][pick_cta.id] = counts["cta"].get(pick_cta.id, 0) + 1
                counts["ps"][ps.id] = counts["ps"].get(ps.id, 1) - 1
                counts["ps"][pick_ps.id] = counts["ps"].get(pick_ps.id, 0) + 1
                fixed["cta"][email] = pick_cta
                fixed["ps"][email] = pick_ps
                moved = True

        if moved:
            repaired.add(email)

    return repaired


def batch_shares(anchors: list[Anchor]) -> dict[str, dict[str, float]]:
    """What share of the batch each fixed line took.

    Three of the five beats come from a pool of twelve sentences. On the last
    batch of ten the top line took 40 / 50 / 50 percent, and these coaches
    compare emails. `lint.py` caps any single line at 35%; this is the number
    it checks.
    """
    shares: dict[str, dict[str, float]] = {}
    total = len(anchors) or 1
    for beat in ("identity", "offer", "cta", "ps"):
        counts: dict[str, int] = {}
        for anchor in anchors:
            line_id = getattr(anchor, beat).id
            counts[line_id] = counts.get(line_id, 0) + 1
        shares[beat] = {k: round(v / total, 3)
                        for k, v in sorted(counts.items(),
                                           key=lambda kv: -kv[1])}
    return shares
