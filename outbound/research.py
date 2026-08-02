"""The research object: the one contract every worker returns.

A worker's prose is not the interface. This is. Each field is either a value or
one of three verdicts, and each carries `_source` naming what settled it, so a
`no` can be argued with rather than believed. The old pipeline's fields were
untyped and unsourced, which meant an empty field and a checked-and-absent
field looked identical, and a soft pass on an audience number burned full walks.

Two rules encoded here:

- **`unclear` passes; only a clear `no` drops a row.** A false kill is
  permanent and invisible. A false pass costs one more research call.
- **A verdict without a source is not a verdict.** `validate` rejects any
  yes/no that names nothing. This is what the verifier enforces, and it is the
  only defence against a worker that reasoned its way to an answer instead of
  fetching one.
"""

from __future__ import annotations

import re
import dataclasses
from dataclasses import dataclass, field, asdict
from datetime import date

MAX_OBSERVATION_PROBLEMS = 6

VERDICTS = ("yes", "no", "unclear")
SELLS_TO = ("corporates", "individuals", "")
COACH_TYPES = ("Business", "Leadership", "Life", "Mindset", "Career",
               "Health", "Fitness", "Executive", "Other", "")


@dataclass
class Research:
    """Everything known about one lead after the research stage."""

    slug: str = ""
    name: str = ""

    # The three floors. Each paired with the source that settled it.
    uae_based: str = "unclear"
    uae_based_source: str = ""
    active_recent: str = "unclear"
    active_recent_source: str = ""
    is_coach: str = "unclear"
    is_coach_source: str = ""

    # Captured, never gated.
    coach_type: str = ""
    coach_type_source: str = ""
    sells_to: str = ""
    sells_to_source: str = ""
    solo: str = "unclear"
    solo_source: str = ""
    audience_size: int | None = None
    audience_source: str = ""
    top_program_price_aed: int | None = None
    price_source: str = ""
    runs_certification: str = "unclear"

    # Contact.
    site_emails: list[str] = field(default_factory=list)
    email: str = ""
    email_status: str = ""          # pass | warn | fail | enriched
    email_source: str = ""

    # The hook, proposed here and verified elsewhere.
    hook: str = ""
    hook_type: str = ""             # WORK | LIFE | METRIC
    hook_source_url: str = ""
    hook_quote: str = ""
    hook_date: str = ""
    hook_verified: str = "proposed"  # proposed | verified | refuted | none

    last_activity: str = ""         # ISO date
    notes: list[str] = field(default_factory=list)

    # What was actually fetched, kept verbatim. Additive and unread by any
    # stage today: the contract exists so evidence stops being discarded one
    # boolean at a time, and so the duplicate fetch it makes unnecessary can be
    # removed against a measurement rather than an argument. See
    # `outbound/observe.py`.
    observations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Research":
        """Build from a worker's JSON, coercing `null` to the field's default.

        A worker that writes `"uae_based_source": null` — the honest JSON for
        "I could not settle this" — produced `AttributeError: 'NoneType' has no
        attribute 'strip'` in `validate`, uncaught. That turned a schema
        violation into what reads as a crashed gate, which is precisely what the
        loaders were written to prevent. Coerced once here rather than with an
        `or ""` at each of the nine use sites, where the tenth would be missed.
        """
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in data.items():
            if key not in known:
                continue
            if value is None:
                spec = known[key]
                if spec.default is not dataclasses.MISSING:
                    value = spec.default
                elif spec.default_factory is not dataclasses.MISSING:
                    value = spec.default_factory()
                else:
                    continue
            fields[key] = value
        return cls(**fields)

    @property
    def passes_floors(self) -> bool:
        return all(getattr(self, f) != "no"
                   for f in ("uae_based", "active_recent", "is_coach"))

    @property
    def failed_floors(self) -> list[str]:
        return [f for f in ("uae_based", "active_recent", "is_coach")
                if getattr(self, f) == "no"]

    @property
    def ready_to_draft(self) -> bool:
        """Everything the drafting stage needs, present and verified."""
        return (self.passes_floors
                and bool(self.email)
                and self.email_status in ("pass", "enriched")
                and self.hook_verified == "verified"
                and bool(self.hook))

    def blockers(self) -> list[str]:
        """Why this lead is not draftable yet, in plain words."""
        reasons = []
        for floor in self.failed_floors:
            reasons.append(f"failed floor: {floor}")
        if not self.email:
            reasons.append("no email address")
        elif self.email_status not in ("pass", "enriched"):
            reasons.append(f"email not verified (status={self.email_status or 'unset'})")
        if not self.hook:
            reasons.append("no hook")
        elif self.hook_verified != "verified":
            reasons.append(f"hook {self.hook_verified}, not verified")
        return reasons


def validate(research: Research) -> list[str]:
    """Schema violations. An empty list means the worker returned a real object.

    Catches the two things a plausible-sounding worker gets wrong: a verdict
    outside the enum (which would silently read as neither yes nor no), and a
    hard yes/no with nothing named as its source.
    """
    problems: list[str] = []

    for field_name in ("uae_based", "active_recent", "is_coach", "solo",
                       "runs_certification"):
        value = getattr(research, field_name)
        if value not in VERDICTS:
            problems.append(f"{field_name}={value!r} is not one of {VERDICTS}")

    for field_name in ("uae_based", "active_recent", "is_coach", "solo"):
        value = getattr(research, field_name)
        source = getattr(research, f"{field_name}_source", "")
        if value in ("yes", "no") and not source.strip():
            problems.append(
                f"{field_name}={value} with no source — a verdict that names "
                f"nothing was reasoned, not fetched"
            )

    if research.coach_type not in COACH_TYPES:
        problems.append(f"coach_type={research.coach_type!r} is not a known segment")
    if research.sells_to not in SELLS_TO:
        problems.append(f"sells_to={research.sells_to!r} is not one of {SELLS_TO}")

    if research.audience_size is not None:
        if not isinstance(research.audience_size, int) or research.audience_size < 0:
            problems.append("audience_size must be a non-negative integer or null")
        elif not research.audience_source.strip():
            problems.append("audience_size given with no source — never guess a count")

    if research.top_program_price_aed is not None and not research.price_source.strip():
        problems.append("top_program_price_aed given with no source")

    if research.hook and not research.hook_source_url.strip():
        problems.append("hook with no source URL — a hook is a citation or it is nothing")
    if research.hook_source_url and not research.hook_quote.strip():
        problems.append("hook cites a URL but quotes nothing from it")

    if research.last_activity:
        try:
            date.fromisoformat(research.last_activity)
        except ValueError:
            problems.append(f"last_activity={research.last_activity!r} is not an ISO date")

    for address in research.site_emails + ([research.email] if research.email else []):
        if address and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", address):
            problems.append(f"malformed address: {address}")

    if research.observations:
        from outbound import observe

        # Capped. A slice returns ten leads' worth of observations, and one
        # worker that got the enum wrong would otherwise bury the floor
        # violations under forty identical lines — which is how a report that
        # flags everything becomes a report nobody reads.
        found = observe.validate_all(observe.load(research.observations))
        problems.extend(found[:MAX_OBSERVATION_PROBLEMS])
        if len(found) > MAX_OBSERVATION_PROBLEMS:
            problems.append(
                f"...and {len(found) - MAX_OBSERVATION_PROBLEMS} more "
                f"observation problem(s) — run `python main.py observe` on "
                f"them for the full list")

    return problems


def schema_help() -> str:
    """The field list, generated from the dataclass rather than written down.

    `research-worker` is told its object must match this module, and nothing
    enumerates the fields for it — the same weak contract that had drafters
    inventing an email address because their return block asked for one. Prose
    listing the fields would drift the first time one changed; this cannot,
    because it IS the dataclass.
    """
    from dataclasses import fields as dataclass_fields

    rows = []
    for f in dataclass_fields(Research):
        kind = getattr(f.type, "__name__", str(f.type))
        rows.append(f"    {f.name:26} {kind}")
    from outbound import observe

    return ("  the schema, one flat object per lead:\n" + "\n".join(rows) +
            "\n  verdict fields take exactly 'yes' | 'no' | 'unclear', and each "
            "carries its own\n  _source naming the page it came from. Fields you "
            "could not settle stay at\n  their defaults; do not invent values to "
            "look complete.\n\n" + observe.schema_help())


def headline(research: Research) -> str:
    """One line: the verdict and what still blocks the lead, without the four
    lines of evidence behind them.

    A slice of ten leads printed in full is about 5 KB, and the orchestrator
    runs this once per slice and again on the merged file — every byte of which
    stays in its context for the rest of the run. A lead that passed the schema
    has nothing in those four lines anybody acts on; the blockers are the part
    that gets read, so they stay on the line.
    """
    problems = validate(research)
    head = "VALID" if not problems else f"INVALID ({len(problems)})"
    verdict = ("PASS" if research.passes_floors
               else f"FAIL ({', '.join(research.failed_floors)})")
    blocked = research.blockers()
    return (f"RESEARCH {research.name or research.slug}: {head}, "
            f"floors {verdict}"
            + (f", blocked ({'; '.join(blocked)})" if blocked else ""))


def needs_a_look(research: Research) -> bool:
    """Whether the full block is worth printing.

    Schema problems only. A blocker is not a reason: this gate runs before the
    hook stage, so *every* lead is blocked on `no hook` at the moment it is
    validated, and triggering on that printed the full block for all of them —
    which is the 14 KB this was meant to cut.
    """
    return bool(validate(research))


def report(research: Research) -> str:
    """The quotable summary a worker returns and an orchestrator cross-checks."""
    problems = validate(research)
    head = "VALID" if not problems else f"INVALID ({len(problems)})"
    verdict = "PASS" if research.passes_floors else f"FAIL ({', '.join(research.failed_floors)})"
    lines = [
        f"RESEARCH {research.name or research.slug}: {head}, floors {verdict}",
        f"  uae={research.uae_based} [{research.uae_based_source or '-'}] "
        f"coach={research.is_coach} [{research.is_coach_source or '-'}] "
        f"active={research.active_recent} [{research.active_recent_source or '-'}]",
        f"  type={research.coach_type or '?'} [{research.coach_type_source or '-'}] "
        f"sells_to={research.sells_to or '?'} [{research.sells_to_source or '-'}]",
        f"  email={research.email or '-'} ({research.email_status or 'unchecked'}) "
        f"hook={research.hook_verified}",
    ]
    for problem in problems:
        lines.append(f"  SCHEMA  {problem}")
    if problems:
        lines.append(schema_help())
    for blocker in research.blockers():
        lines.append(f"  blocked  {blocker}")
    return "\n".join(lines)
