"""The hook proposal: what a worker claims it found, checked before anyone buys it.

This closes F4, which named the hook as *the only consequential artifact with no
mechanical gate*. Research has a schema. Observations have a schema. The hook —
the one sentence a stranger reads first, the one thing this machine refuses to
invent — arrived as prose in a report and went straight to an independent
verifier, who re-fetched the page and certified the wording.

## Why a gate here rather than one stage later

**The hook was certified before it was linted, and the two disagreed.** Six of
twelve drafts on `2026-08-01-q1` had to alter text a verifier had confirmed word
for word: an em-dash, spaced hyphens, "touchpoints" off the jargon list, and
four figures. Every one of those is a rule the linter has always held and the
hook stage never ran.

That ordering is F11's shape again — a constraint applied after the point where
honouring it was free. When a quote fails the voice rules, the honest repair is
to **pick a different quote**, and only the worker can do that: it has the page
open and the verifier has not run. One stage later the drafter has neither the
alternatives nor the authority, so it edits the citation instead, and a hook
squeezed after certification is a citation drifting from its source.

So: propose, run this, fix by re-choosing, then send it to the verifier.

## What it will not do

**It does not verify anything.** The quote being well-formed says nothing about
whether it is on the page, and the live re-fetch stays exactly where it is. A
worker that reads a PASS here as permission to skip the verifier has broken the
only mechanism in this system that has ever caught a fabricated claim.

**It never rewrites a quote.** Every finding names the quote as the thing to
change. A gate that offered a repaired string would be inviting a worker to
put words in the recipient's mouth — the failure it exists to prevent, wearing
a helpful face.

## The one URL rule that is not about words

harvestapi builds LinkedIn post URLs from a text-derived slug, and a post with
no usable text gets an empty one: `/posts/mauricehellemons_-activity-7356…`
against a working `/posts/lucycrussell_i-put-my-phone-on-airplane-mode-…`. The
content is real and was paid for. The URL 404s. An email cannot cite a page the
reader cannot open, so the citation is unusable however true the quote is — and
that lead lost its hook to a REFUTED verdict which cost a full verifier pass to
reach. It is a string check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field
from datetime import date

# The CRM's `Hook Type` options, which have been a select since the beginning
# precisely so reply rate can be tested against them. Mirrored from the one
# place that owns them rather than restated.
from audit.airtable import HOOK_TYPES


@dataclass
class HookProposal:
    """One proposed hook, before an independent verifier has seen it."""

    lead_key: str = ""
    # The join that proves this came from something actually retrieved rather
    # than composed. Post-flip it is required unless the proposal declares an
    # escalation, and `validate(..., shortlists=...)` checks the quote really is
    # a piece of that observation's stored text.
    observation_id: str = ""
    quote: str = ""              # verbatim, theirs
    line: str = ""               # the authored clause — what the writer took
    hook_type: str = ""          # one of HOOK_TYPES
    source_url: str = ""
    published_at: str = ""       # ISO date
    # The bounded escalation. A hook with no `observation_id` is legal only when
    # the worker says it went and got one, and names the rung it walked — the
    # difference between "the shortlist did not hold" and "this came from
    # nowhere" is the whole of what `select --against`'s `unobserved` counts.
    escalated: bool = False
    escalation_rung: str = ""
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "HookProposal":
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in (data or {}).items():
            if key not in known:
                continue
            if value is None:
                value = [] if key == "notes" else False if key == "escalated" else ""
            fields[key] = value
        fields["escalated"] = bool(fields.get("escalated"))
        return cls(**fields)


# `/posts/<slug>_-activity-` and `/posts/_-activity-` are the shapes harvestapi
# emits when the post has no text to build a slug from. Matched on the empty
# segment between the underscore and `-activity`, because that is the defect:
# a real URL always carries words there.
_DEAD_LI_POST = re.compile(r"/posts/[^/?#]*?_-activity-", re.I)


def unusable_citation(url: str) -> str:
    """Why this URL cannot be cited, or "" if it can be.

    Only structural impossibility. Whether the page says what the quote says is
    the verifier's question and stays there.
    """
    text = (url or "").strip()
    if not text:
        return "no source_url — a hook is a citation or it is nothing"
    if not text.lower().startswith(("http://", "https://")):
        return f"source_url {text!r} is not a fetchable URL"
    if _DEAD_LI_POST.search(text):
        return ("the post URL has an empty slug "
                "(`/posts/<name>_-activity-…`), which is what harvestapi builds "
                "when a post has no text to name it. It 404s. The content is "
                "real and was paid for, and the citation is still unusable — "
                "an email cannot point at a page the reader cannot open")
    return ""


def _flatten(text: str) -> str:
    """Whitespace-normalised, for comparing a quote against stored text.

    Only whitespace. Not case, not punctuation: a quote is meant to be verbatim,
    and a comparison that forgave a changed word would forgive exactly the drift
    it exists to catch. Line breaks are the one thing that legitimately differs
    between a scraped post and a sentence pulled out of it.
    """
    return " ".join((text or "").split())


def check_join(proposal: HookProposal, shortlists: dict) -> list[str]:
    """The quote against the observation it names. Ban #3, made mechanical.

    "No invented specifics — if it cannot be cited, it does not exist" was a
    sentence an agent was asked to remember, for as long as there was nothing to
    check it against. Post-flip there is: `select` hands the worker three
    candidates carrying their observations' verbatim text, so a quote either is
    a contiguous piece of one of them or it is not.

    `shortlists` maps `lead_key` to that lead's candidates, from `select --out`.

    **An escalation is the one legal way to have no `observation_id`**, and it
    has to be declared. Before the flip a blank id was ordinary — the hook stage
    did its own fetching and most hooks had no stored observation behind them.
    Now a blank id means one of two opposite things: the worker went and got
    something the shortlist did not have, or it composed a hook from nothing.
    Only the worker can say which, so it has to.
    """
    lead = shortlists.get(proposal.lead_key) or []

    if not proposal.observation_id.strip():
        if not proposal.escalated:
            return ["no observation_id and no escalation declared — post-flip a "
                    "hook comes from the shortlist or from a rung you walked and "
                    "named. A hook with neither has no provenance at all"]
        if not proposal.escalation_rung.strip():
            return ["escalated with no rung named — which rung was walked is "
                    "what makes the escalation rate readable, and an escalation "
                    "nobody can attribute is indistinguishable from a guess"]
        return []

    if proposal.escalated:
        return ["escalated AND joined to an observation — one or the other. If "
                "the shortlist held, this was not an escalation; if it did not, "
                "the observation_id belongs to something else"]

    match = next((c for c in lead
                  if (c.get("obs_id") or "") == proposal.observation_id), None)
    if match is None:
        if not lead:
            return [f"observation_id {proposal.observation_id!r} names nothing — "
                    f"this lead has no shortlist, so there was nothing to pick "
                    f"from and any hook here is an escalation or an invention"]
        return [f"observation_id {proposal.observation_id!r} is not in this "
                f"lead's shortlist of {len(lead)} — the ranker offered "
                f"{', '.join(c.get('obs_id', '?') for c in lead)}"]

    if _flatten(proposal.quote) not in _flatten(match.get("quote", "")):
        return ["the quote is not a contiguous piece of the observation it "
                "names. Either it was edited, or two sentences were fused, or "
                "it came from somewhere else — and all three produce a citation "
                "the verifier will refute after this stage has already paid for "
                "it. Quote it exactly, or pick a different candidate"]
    return []


def validate(proposal: HookProposal, *, today: date | None = None,
             shortlists: dict | None = None) -> list[str]:
    """Everything mechanical, before a verifier is spent on it.

    Ordered structural first, then voice, so a worker reading the list fixes the
    thing that makes the rest moot.

    `shortlists` turns on the join check. It is optional so the single-lead
    repair path in `outbound-draft` still works on a proposal with no batch
    behind it — but a batch run passes it, and the batch skill says so.
    """
    from outbound import lint

    problems: list[str] = []
    today = today or date.today()

    if shortlists is not None:
        problems.extend(check_join(proposal, shortlists))

    if not proposal.quote.strip():
        problems.append("no quote — a hook is quoted from their own words")
    if not proposal.line.strip():
        problems.append(
            "no line — the authored clause is the only part of the hook a "
            "person writes, and a quote handed back with nothing taken from it "
            "is the failure the hook rules call 'no writer in it'")
    if proposal.hook_type and proposal.hook_type not in HOOK_TYPES:
        problems.append(
            f"hook_type={proposal.hook_type!r} is not one of "
            f"{'/'.join(HOOK_TYPES)} — Airtable will reject the CRM row")

    unusable = unusable_citation(proposal.source_url)
    if unusable:
        problems.append(unusable)

    if not proposal.published_at.strip():
        problems.append(
            "no published_at — requirement 3 is that a hook is cited, and a "
            "post with no date cannot be shown to be recent")
    else:
        try:
            published = date.fromisoformat(proposal.published_at)
        except ValueError:
            problems.append(
                f"published_at={proposal.published_at!r} is not an ISO date")
        else:
            if published > today:
                problems.append(
                    f"published_at={proposal.published_at} is in the future — "
                    f"a date nobody could have read is a date nobody fetched")

    # The voice rules, run here rather than three stages later. `check_voice`
    # returns (failures, warnings) over a whole body; the hook beat is a
    # fragment, so only the rules that are about the WORDS apply — a hook has
    # no sign-off and no word budget of its own.
    beat = f"{proposal.quote} {proposal.line}"
    for problem in lint.check_voice_fragment(beat):
        problems.append(f"{problem} — pick a different quote or reword the "
                        f"clause, do NOT edit their words")

    return problems


def validate_all(proposals: list, *, today: date | None = None,
                 shortlists: dict | None = None) -> list[str]:
    problems = []
    for index, proposal in enumerate(proposals):
        for problem in validate(proposal, today=today, shortlists=shortlists):
            problems.append(f"hook[{index}] ({proposal.lead_key or '?'}) {problem}")
    return problems


def shortlists_from(selections) -> dict:
    """`lead_key` -> that lead's candidate dicts, from a `select --out` file.

    Accepts the file's own shape (`{"selections": [...]}`) or the bare list, the
    same tolerance every loader here has, because the two are equally likely to
    be what somebody has in hand.
    """
    rows = selections.get("selections") if isinstance(selections, dict) \
        else selections
    out = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        key = (row.get("lead_key") or "").strip()
        if key:
            out[key] = [c for c in (row.get("shortlist") or [])
                        if isinstance(c, dict)]
    return out


def load(data) -> list:
    """One proposal or a list of them, the shape every gate here accepts."""
    rows = data if isinstance(data, list) else [data]
    return [HookProposal.from_dict(row) for row in rows if isinstance(row, dict)]


def schema_help() -> str:
    """The field list, generated from the dataclass rather than written down."""
    from dataclasses import fields as dataclass_fields

    rows = []
    for f in dataclass_fields(HookProposal):
        kind = getattr(f.type, "__name__", str(f.type))
        rows.append(f"    {f.name:18} {kind}")
    return ("  one object per proposed hook:\n" + "\n".join(rows)
            + f"\n  hook_type is one of {HOOK_TYPES}\n"
              "  quote is VERBATIM theirs. line is the clause YOU wrote.\n"
              "  observation_id names the shortlist entry the quote came from. "
              "It may be\n  blank ONLY with escalated=true and an "
              "escalation_rung: post-flip a hook\n  comes from the shortlist or "
              "from a rung you walked and named, and a hook\n  with neither has "
              "no provenance. Escalations are what `metrics` counts.")


def report(proposals: list, *, today: date | None = None,
           shortlists: dict | None = None) -> str:
    """The quotable summary, in the shape `observe.report` already uses."""
    problems = validate_all(proposals, today=today, shortlists=shortlists)
    head = "VALID" if not problems else f"INVALID ({len(problems)})"
    joined = sum(1 for p in proposals if p.observation_id.strip())
    escalated = sum(1 for p in proposals if p.escalated)

    lines = [
        f"HOOK: {head}, {len(proposals)} proposal(s), "
        f"{joined} joined to a stored observation, {escalated} escalated",
    ]
    if shortlists is None:
        lines.append("  no shortlist given, so the quote was NOT checked "
                     "against the observation it names — pass --against "
                     "work/select.json on a batch run")
    for proposal in proposals:
        if proposal.escalated:
            lines.append(f"  ESCALATED {proposal.lead_key or '?'} on "
                         f"{proposal.escalation_rung or '(unnamed rung)'} — the "
                         f"shortlist did not hold, which is the number the flip "
                         f"is judged on")
    for problem in problems:
        lines.append(f"  CHECK   {problem}")
    if problems:
        lines.append(schema_help())
    lines.append("  NOT VERIFICATION. Nothing here has looked at the page. The "
                 "verifier's live re-fetch is the only thing that has ever "
                 "caught a fabricated claim, and it still runs.")
    return "\n".join(lines)
