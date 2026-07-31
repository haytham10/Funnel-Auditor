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
from dataclasses import dataclass, field, asdict
from datetime import date

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

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Research":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

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

    return problems


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
    for blocker in research.blockers():
        lines.append(f"  blocked  {blocker}")
    return "\n".join(lines)
