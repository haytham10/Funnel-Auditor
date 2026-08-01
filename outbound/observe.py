"""The observation: one thing that was actually fetched, kept verbatim.

The research contract answers *floors*, and it answers them well. What it does
not do is carry evidence forward. It stores a `_source` **string** per verdict —
a URL or a page name — so the LinkedIn post that settled `active_recent`, which
is the exact material a hook is made of, is read once, reduced to a boolean, and
thrown away. Then the hook stage pays to fetch it again. That is F2 and F1 of
docs/proposals/2026-08-01-hook-retrieval.md, and this module is the record that
makes the second fetch unnecessary.

**Additive, and nothing consumes it yet.** A research object may now carry
observations alongside its verdicts; no stage reads them, `hook-worker` is
untouched, and the duplicate fetch is still made on purpose so the ledger can
price it. What lands here is the contract and its gate, so that when selection
does arrive it ranks records that were schema-checked at the moment they were
written rather than prose assembled later.

Two things this contract is built to make mechanical, once something reads it:

- **`author`.** Ban #7 of the hook rules is "no third-party coverage". Today
  that is a sentence an agent is asked to remember. It is `author == "self"`.
- **`published_at`.** Ban #6 is "no stale news as fresh". That is a date
  comparison, and it is also the evidence the activity floor never had — F3,
  where `latest_activity_date` found zero usable dates across nine sites and
  ~220,000 characters, so `active_recent` came back `unclear` for effectively
  every lead and the floor did nothing.

`obs_id` is generated from the content when left blank, the same convention
Copy Assets uses for `Line ID` — so it is not something a worker can get wrong,
and it is the join that will let a hook prove it came from something actually
retrieved rather than something composed.

`text` is verbatim. No check can prove that, which is exactly why it is stated
here rather than assumed: a summarised observation reads fine, ranks fine, and
produces a hook whose quote is not on the page — the one failure the independent
verifier exists to catch, arriving through the one door it does not watch.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import date, datetime

PLATFORMS = ("linkedin", "instagram", "youtube", "podcast", "facebook",
             "tiktok", "site", "web")
KINDS = ("post", "episode", "video", "about", "framework", "result", "bio")
AUTHORS = ("self", "third_party", "unknown")

# The kinds that are a piece of content rather than a fact about a profile. An
# observation of one of these with no text was reasoned, not fetched — the same
# rule as a research verdict that names no source.
CONTENT_KINDS = ("post", "episode", "video", "about", "framework")

# How an observation may have been come by. `apify:<key>` is checked against the
# live actor map, so an observation cannot claim a retrieval path that does not
# exist. The two free rungs are model-side and reported on trust, exactly as
# they are in the ledger.
FREE_SOURCES = ("tier0", "websearch", "webfetch")


@dataclass
class Observation:
    """One page, post or episode, as it was when we read it."""

    obs_id: str = ""
    lead_key: str = ""
    platform: str = ""
    url: str = ""                # the page actually fetched
    fetched_at: str = ""         # ISO datetime — when WE fetched it
    published_at: str = ""       # ISO date | "" — when THEY published it
    author: str = "unknown"      # self | third_party | unknown
    kind: str = ""
    text: str = ""               # verbatim, never summarised
    cost_usd: float = 0.0
    retrieved_by: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Observation":
        """Build from a worker's JSON, dropping unknown keys and coercing
        `null` to the field's default — the same coercion `Research.from_dict`
        does, and for the same reason: a worker writing `"published_at": null`
        is being honest, and it must not surface as a crashed gate."""
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in data.items():
            if key not in known:
                continue
            if value is None:
                value = known[key].default
            fields[key] = value
        obs = cls(**fields)
        if not obs.obs_id:
            obs.obs_id = make_id(obs)
        return obs

    @property
    def days_old(self) -> int | None:
        """Days since it was published, or None if it carries no date."""
        try:
            return (date.today() - date.fromisoformat(self.published_at)).days
        except ValueError:
            return None


def make_id(obs: Observation) -> str:
    """A stable id derived from what the observation IS.

    Content-derived rather than a counter, so the same post observed twice — by
    two workers, or by a re-run — collapses to one id instead of two records
    that look independent. The text is truncated because a caption edited by a
    word is the same observation, and a hash over the whole body would say
    otherwise.
    """
    seed = f"{obs.lead_key}|{obs.url}|{obs.published_at}|{obs.text[:200]}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def validate(obs: Observation, *, today: date | None = None) -> list[str]:
    """Schema violations. An empty list means the worker returned a real record.

    Catches what a plausible-sounding worker gets wrong: a platform or kind
    outside the enum, a piece of content with nothing in it, a date that will
    not parse or has not happened, and a retrieval path no rung of this machine
    actually has.
    """
    problems: list[str] = []
    today = today or date.today()

    if obs.platform not in PLATFORMS:
        problems.append(f"platform={obs.platform!r} is not one of {PLATFORMS}")
    if obs.kind not in KINDS:
        problems.append(f"kind={obs.kind!r} is not one of {KINDS}")
    if obs.author not in AUTHORS:
        problems.append(f"author={obs.author!r} is not one of {AUTHORS}")

    if not obs.url.strip():
        problems.append("no url — an observation names the page it came from")
    if obs.kind in CONTENT_KINDS and not obs.text.strip():
        problems.append(
            f"kind={obs.kind} with no text — an observation that quotes "
            f"nothing was reasoned, not fetched")

    if not obs.fetched_at.strip():
        problems.append("no fetched_at — without it staleness is unanswerable")
    else:
        try:
            datetime.fromisoformat(obs.fetched_at)
        except ValueError:
            problems.append(f"fetched_at={obs.fetched_at!r} is not an ISO datetime")

    if obs.published_at.strip():
        try:
            published = date.fromisoformat(obs.published_at)
        except ValueError:
            problems.append(f"published_at={obs.published_at!r} is not an ISO date")
        else:
            if published > today:
                problems.append(
                    f"published_at={obs.published_at} is in the future — a "
                    f"date nobody could have read is a date nobody fetched")

    if not obs.retrieved_by.strip():
        problems.append("no retrieved_by — an observation names the rung it cost")
    elif obs.retrieved_by not in FREE_SOURCES:
        if not obs.retrieved_by.startswith("apify:"):
            problems.append(
                f"retrieved_by={obs.retrieved_by!r} is not one of {FREE_SOURCES} "
                f"or apify:<actor_key>")
        else:
            from audit.apify import ACTORS
            key = obs.retrieved_by.split(":", 1)[1]
            if key not in ACTORS:
                problems.append(
                    f"retrieved_by names apify:{key}, which is not an actor "
                    f"this machine has")

    if obs.cost_usd is None or obs.cost_usd < 0:
        problems.append("cost_usd must be a non-negative number")

    return problems


def validate_all(observations: list[Observation],
                 *, today: date | None = None) -> list[str]:
    """Every observation's problems, each prefixed with which one it was."""
    problems = []
    for index, obs in enumerate(observations):
        for problem in validate(obs, today=today):
            problems.append(f"observation[{index}] {problem}")
    return problems


def load(data) -> list[Observation]:
    """One observation or a list of them, as `lint` accepts one draft or many."""
    rows = data if isinstance(data, list) else [data]
    return [Observation.from_dict(row) for row in rows if isinstance(row, dict)]


def schema_help() -> str:
    """The field list, generated from the dataclass rather than written down.

    Same reason as `research.schema_help`: prose listing the fields drifts the
    first time one changes, and this cannot, because it IS the dataclass.
    """
    from dataclasses import fields as dataclass_fields

    rows = []
    for f in dataclass_fields(Observation):
        kind = getattr(f.type, "__name__", str(f.type))
        rows.append(f"    {f.name:26} {kind}")
    return ("  observations, one object per page or post actually fetched:\n"
            + "\n".join(rows)
            + f"\n  platform is one of {PLATFORMS}\n"
              f"  kind is one of {KINDS}\n"
              f"  author is one of {AUTHORS} — 'self' means THEY wrote it\n"
              "  text is VERBATIM. Never summarise it: a hook is quoted from "
              "this, and an\n  independent verifier re-fetches the page to "
              "check the quote is really there.\n"
              "  obs_id generates from the content if you leave it blank.")


def report(observations: list[Observation], *,
           today: date | None = None) -> str:
    """The quotable summary, in the shape `research.report` already uses."""
    problems = validate_all(observations, today=today)
    head = "VALID" if not problems else f"INVALID ({len(problems)})"
    dated = sum(1 for o in observations if o.published_at)
    theirs = sum(1 for o in observations if o.author == "self")

    lines = [
        f"OBSERVE: {head}, {len(observations)} observation(s) over "
        f"{len({o.lead_key for o in observations if o.lead_key})} lead(s)",
        f"  {dated} dated, {theirs} written by the lead themselves, "
        f"${sum(o.cost_usd or 0.0 for o in observations):.4f} to fetch",
    ]
    for problem in problems:
        lines.append(f"  SCHEMA  {problem}")
    if problems:
        lines.append(schema_help())
    return "\n".join(lines)
