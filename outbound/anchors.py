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
from dataclasses import dataclass, field
from pathlib import Path

COPY_DIR = Path(__file__).resolve().parent.parent / "copy"

EXACT_MATCH_RATIO = 0.70    # segment-matched line 70% of the time, generic 30%


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
            numbers.add(round(100 * self.total_meetings / self.total_sent, 1))
        return {n for n in numbers if isinstance(n, int)}


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


# ------------------------------------------------------------------ the lines


@dataclass
class Line:
    id: str
    line: str
    meta: dict = field(default_factory=dict)


def _read_lines(name: str) -> list[Line]:
    path = COPY_DIR / name
    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return [Line(id=row["id"], line=row["line"],
                 meta={k: v for k, v in row.items() if k not in ("id", "line")})
            for row in rows]


@dataclass
class CopyBank:
    identity: list[Line]
    offer: list[Line]
    cta: list[Line]
    ps: list[Line]

    @classmethod
    def load(cls) -> "CopyBank":
        return cls(
            identity=_read_lines("identity.csv"),
            offer=_read_lines("offer.csv"),
            cta=_read_lines("cta.csv"),
            ps=_read_lines("ps.csv"),
        )


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


def draw_weighted(lines: list[Line], email: str, salt: str) -> Line:
    """Pick by the `roll_1_100` range each line declares."""
    roll = _roll(email, salt, 100)
    for line in lines:
        span = line.meta.get("roll_1_100", "")
        if "-" in span:
            low, _, high = span.partition("-")
            if int(low) <= roll <= int(high):
                return line
    return lines[roll % len(lines)]


def draw_identity(lines: list[Line], email: str, *,
                  coach_type: str, sells_to: str) -> Line:
    """Match on segment AND audience, with a 70/30 exact-to-generic split.

    Falls through in order: exact segment + exact audience -> exact segment,
    any audience -> generic (`Any`). An unknown `sells_to` never invents a
    match; it just drops to the segment-only pool, which is honest.
    """
    def pool(type_match, sells_match) -> list[Line]:
        return [l for l in lines
                if type_match(l.meta.get("coach_type", ""))
                and sells_match(l.meta.get("sells_to", ""))]

    exact_both = pool(lambda t: t == coach_type,
                      lambda s: bool(sells_to) and s == sells_to)
    exact_type = pool(lambda t: t == coach_type, lambda s: s in ("any", ""))
    generic = pool(lambda t: t == "Any", lambda s: True)

    exact = exact_both + exact_type
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

    def as_prompt_block(self) -> str:
        """What the drafting model actually sees."""
        return "\n".join([
            "ANCHOR LINES (hand-written by Haytham — match their voice; you may",
            "re-voice for flow, you may not change what they claim):",
            f"  identity [{self.identity.id}]: {self.identity.line}",
            f"  offer    [{self.offer.id}]: {self.offer.line}",
            f"  cta      [{self.cta.id}]: {self.cta.line}",
            f"  ps       [{self.ps.id}]: {self.ps.line}",
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
    """The whole draw for one lead. Deterministic given the same address."""
    bank = bank or CopyBank.load()
    facts = facts or load_facts()
    identity = draw_identity(bank.identity, email,
                             coach_type=coach_type, sells_to=sells_to)
    drawn_segment = identity.meta.get("coach_type", "")
    segment = coach_type if drawn_segment == coach_type else ""
    return Anchor(
        identity=identity,
        offer=draw_weighted(bank.offer, email, "offer"),
        cta=draw_weighted(bank.cta, email, "cta"),
        ps=draw_weighted(bank.ps, email, "ps"),
        segment=segment,
        allowed_numbers=all_numbers(facts),
    )


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
