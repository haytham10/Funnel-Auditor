"""Which leads are worth spending on, before anything is spent.

A scraped list is mostly not the ICP. This dump is 237 profiles and the three
floors already know how to read most of them for free, off text that arrived
with the list — so asking them first is the difference between paying to search
237 addresses and paying to search the hundred or so that could qualify.

**It sorts; it barely drops.** Three tiers:

    RUN     all three floors read `yes`
    HOLD    a floor reads `unclear` — no UAE word, no coach word, no posts
    DROP    a floor reads a clear `no`

`unclear` is HOLD and never DROP, which is `qualify`'s rule and not a new one:
a false kill is permanent and invisible, a false pass costs one research call.
A missing "Dubai" in a bio is the absence of evidence, and this stage is
explicitly not allowed to read it as evidence of absence. HOLD rows are written
out with their verdicts, cost nothing further, and are a queue rather than a
graveyard.

**The floors are `qualify`'s, called, not re-implemented.** `check_uae`,
`check_coach` and `check_active` are three-valued, carry the source that settled
each answer, and have already absorbed a batch's worth of corrections — the
subject/prose split, the word-bounded matching, the three-part bar before a
`no` on occupation. A second ICP here would drift from the one `research-worker`
answers to, and the two would disagree in a way nobody would notice for a batch.

## The one place this stage may read absence as a `no`

`qualify.activity_from_observations` moves the activity floor **upward only**,
on purpose: a research worker's observations are a sample of what it happened
to fetch, so a stale set means the retrieval was old, not that the lead is.

A profile scrape is not a sample. `latestPosts` is what the account has, read
off the platform on the dump's own date, so "the newest of twelve is eight
months old" is a measurement of the lead rather than of our retrieval. That is
the whole justification, it is narrow, and it is why this module makes the call
itself instead of loosening the rule for everybody: `activity_from_observations`
is untouched, and a caller without a complete corpus gets exactly what it got
before.

`complete_corpus=False` is the default. A stale set then reads `unclear` and
lands in HOLD.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date

from outbound import qualify

RUN, HOLD, DROP = "RUN", "HOLD", "DROP"

# An account name that is a place or an organisation rather than a person. Used
# ONLY to confirm a `no` that `check_coach` already returned — never to produce
# one. A coach may perfectly well name their practice "The Studio".
_ORGANISATION = (
    "studio", "gym", "clinic", "centre", "center", "academy", "community",
    "hub", "agency", "salon", "spa", "cafe", "restaurant", "collective",
    "club", "society", "school", "institute",
)


@dataclass
class Triage:
    """One lead's tier, with every verdict that produced it."""

    lead_key: str = ""
    name: str = ""
    tier: str = HOLD
    reason: str = ""
    uae: str = qualify.UNCLEAR
    uae_source: str = ""
    coach: str = qualify.UNCLEAR
    coach_source: str = ""
    active: str = qualify.UNCLEAR
    active_source: str = ""
    observations: int = 0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def line(self) -> str:
        return (f"{self.tier:5} {self.name[:34]:34} "
                f"uae={self.uae:7} coach={self.coach:7} active={self.active:7} "
                f"| {self.reason}")


def _text_of(lead, observations) -> str:
    """Everything this lead said about themselves, for the prose floors.

    The bio and the captions, not a summary of them. `check_uae` may only ever
    return `yes` off prose — its subject/prose split is the fix for a lead
    killed by a "based in Singapore" that described a past employer — so adding
    captions here can raise a verdict and cannot lower one.
    """
    parts = [getattr(lead, "headline", ""), getattr(lead, "company", "")]
    parts += [obs.text for obs in observations if obs.text]
    return "\n".join(p for p in parts if p)


def _activity(observations, *, complete_corpus: bool,
              today: date | None = None) -> qualify.Verdict:
    """The activity floor, and the only asymmetry this module adds.

    With a complete corpus, the newest post settles the floor either way — the
    module docstring is the argument. Without one, this is exactly
    `activity_from_observations` followed by `check_active`, which is what every
    other caller gets.
    """
    today = today or date.today()
    when, why = qualify.activity_from_observations(observations, today=today)
    if when is not None:
        return qualify.check_active(last_seen=when, today=today, source="instagram")
    if not complete_corpus:
        return qualify.Verdict(qualify.UNCLEAR, "instagram", why)

    dated = []
    for obs in observations:
        if (obs.author or "").lower() == "third_party":
            continue                    # their post about us is not our post
        try:
            when = date.fromisoformat((obs.published_at or "").strip())
        except ValueError:
            continue
        if when <= today:
            dated.append(when)
    if not dated:
        # A complete corpus with no dated post at all is a private or empty
        # account, which is nothing to judge. Absence of the corpus is not a
        # measurement of the lead.
        return qualify.Verdict(qualify.UNCLEAR, "instagram",
                               "no dated post in the dump")
    newest = max(dated)
    verdict = qualify.check_active(last_seen=newest, today=today,
                                   source="instagram (complete corpus)")
    return verdict


def triage_lead(lead, observations, *, complete_corpus: bool = False,
                today: date | None = None) -> Triage:
    """One lead's tier. Free, offline, and it fetches nothing."""
    from outbound.fetch import lead_key as key_of

    observations = list(observations or [])
    text = _text_of(lead, observations)
    headline = getattr(lead, "headline", "") or ""

    uae = qualify.check_uae(city=getattr(lead, "city", ""), text=text,
                            domain=getattr(lead, "site_url", ""),
                            headline=headline)
    coach = qualify.check_coach(headline=headline, text=text)
    active = _activity(observations, complete_corpus=complete_corpus, today=today)

    name = getattr(lead, "name", "") or ""
    result = Triage(
        lead_key=key_of(lead), name=name,
        uae=uae.value, uae_source=f"{uae.source}: {uae.evidence}".strip(": "),
        coach=coach.value,
        coach_source=f"{coach.source}: {coach.evidence}".strip(": "),
        active=active.value,
        active_source=f"{active.source}: {active.evidence}".strip(": "),
        observations=sum(1 for obs in observations if obs.kind == "post"),
    )

    if active.value == qualify.NO:
        result.tier, result.reason = DROP, f"stale — {active.evidence}"
    elif coach.value == qualify.NO:
        # `check_coach` needs a stated non-coach occupation AND no coach marker
        # anywhere before it says no, which is already a high bar. The name
        # check only records WHY, so a DROP list is arguable rather than a list
        # of verdicts to take on trust.
        organisation = next((word for word in _ORGANISATION
                             if word in name.lower()), "")
        result.tier = DROP
        result.reason = (f"not a coach — {coach.evidence}"
                         + (f"; account name reads as an organisation "
                            f"({organisation})" if organisation else ""))
    elif uae.value == qualify.NO:
        result.tier, result.reason = DROP, f"not UAE-based — {uae.evidence}"
    elif uae.value == coach.value == active.value == qualify.YES:
        result.tier, result.reason = RUN, "all three floors read yes"
    else:
        unclear = [label for label, verdict in
                   (("uae", uae), ("coach", coach), ("active", active))
                   if verdict.value != qualify.YES]
        result.tier = HOLD
        result.reason = ("unclear on " + ", ".join(unclear)
                         + " — evidence absent, never evidence against")
    return result


def triage_all(leads, observations, *, complete_corpus: bool = False,
               today: date | None = None) -> list[Triage]:
    """Every lead, joined to its own observations on `fetch.lead_key`."""
    from outbound.fetch import lead_key as key_of

    pools: dict[str, list] = {}
    for obs in observations or []:
        pools.setdefault(obs.lead_key, []).append(obs)
    return [triage_lead(lead, pools.get(key_of(lead), []),
                        complete_corpus=complete_corpus, today=today)
            for lead in leads]


def counts(results: list[Triage]) -> dict:
    out = {RUN: 0, HOLD: 0, DROP: 0}
    for result in results:
        out[result.tier] = out.get(result.tier, 0) + 1
    return out


def report(results: list[Triage], *, show_drops: int = 60) -> str:
    """The tier counts, and then every DROP in full.

    The drops are printed rather than summarised because a drop is the only
    irreversible thing this stage does, and the operator reading them is the
    gate — there is no exit code here that substitutes for that.
    """
    tally = counts(results)
    lines = [f"TRIAGE: {len(results)} leads — "
             f"RUN {tally[RUN]}, HOLD {tally[HOLD]}, DROP {tally[DROP]}"]

    holds: dict[str, int] = {}
    for result in results:
        if result.tier == HOLD:
            holds[result.reason] = holds.get(result.reason, 0) + 1
    for reason, n in sorted(holds.items(), key=lambda pair: -pair[1]):
        lines.append(f"  HOLD {n:3}  {reason}")

    drops = [r for r in results if r.tier == DROP]
    if drops:
        lines.append(f"  the {len(drops)} dropped, in full — read them, "
                     f"they are the only irreversible thing here:")
        for result in drops[:show_drops]:
            lines.append(f"    {result.name[:38]:38} {result.reason}")
        if len(drops) > show_drops:
            lines.append(f"    ... and {len(drops) - show_drops} more in --out")
    return "\n".join(lines)


def selected(results: list[Triage], tier: str = RUN) -> set[str]:
    return {r.lead_key for r in results if r.tier == tier}
