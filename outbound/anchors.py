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

        Airtable exists so Haytham can change a line without touching code, and
        the CSVs exist so the machine still runs when Airtable does not. The
        order is the whole design:

        1. **Live Airtable**, when `AIRTABLE_API_KEY` is set. Dormant today —
           no key is in the environment — and it activates with no other change
           the moment one is.
        2. **`copy/_airtable.json`**, the snapshot written by
           `main.py copy-sync`. That is the working path right now: Airtable's
           MCP is the model's tool, not Python's, so a skill fetches the records
           and pipes them to the sync, which validates before writing.
        3. **`copy/*.csv`**, committed and always present.

        Every path above the CSVs has already passed `copy_sync.validate`, so a
        line reaching a draft has been checked for invented numbers, relabelled
        segments, and roll ranges that leave leads drawing nothing. A live fetch
        that fails validation falls through rather than shipping — better a
        slightly stale line than an unchecked one.

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

        if forced != "csv":
            if forced != "snapshot":
                try:
                    from audit import airtable
                    if airtable.available():
                        records = airtable.copy_assets()
                        lines, _ = copy_sync.normalize_records(records)
                        if lines and not copy_sync.validate(lines):
                            _BANK = cls.from_lines(lines, "airtable")
                            return _BANK
                except Exception:
                    # A dead key, a rename, a network blip. Never fatal: falling
                    # through to a checked snapshot beats stopping the run.
                    pass

            snapshot = copy_sync.load_snapshot()
            if snapshot:
                _BANK = cls.from_lines(snapshot, "snapshot")
                return _BANK

        _BANK = cls.from_csv()
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
    # herself. A cold reader caught the mirror of it — an individuals-flavoured
    # generic reaching a corporate seller — and said the number "lands on a
    # market he does not sell into". Both directions are the same bug.
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

    widened = all_numbers(facts)
    return {
        lead["email"]: Anchor(
            identity=identity[lead["email"]],
            offer=fixed["offer"][lead["email"]],
            cta=fixed["cta"][lead["email"]],
            ps=fixed["ps"][lead["email"]],
            segment=segments[lead["email"]],
            allowed_numbers=widened,
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

    from outbound.lint import WORD_MAX

    def fits(beats: dict, line: str) -> bool:
        """The swap must not push the email over the word ceiling.

        A ps is 11 to 26 words, so exchanging one for another moves the total by
        up to 15 — enough to tip an email that was sitting at the cap. Two did,
        and were rejected for length by a change nobody wrote.
        """
        from outbound.export import assemble_body
        body = assemble_body({**beats, "ps": line}, greeting_name="Name")
        return len(body.split()) <= WORD_MAX

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
