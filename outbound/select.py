"""Which observation a hook would be made from, chosen without fetching anything.

The hook stage today is the one consequential stage that searches. `hook-worker`
opens a context per lead, walks a ladder written in prose, and fetches — after
`research-worker` has already fetched, for the same lead, and thrown the material
away (F1, F2). This module is the other half of that: a ranking over the
observations P1 kept, so that finding a hook becomes selection rather than search.

**It runs alongside the hook stage and nothing consumes it.** `hook-worker` still
fetches, still proposes, and is not edited. What lands here is the ranker and one
measurement, `--against`, which asks the only question that can settle whether
the fetch is removable: **would this have picked the same evidence?**

That question has never had a number. `data/runs/` has never recorded a
`li_posts` fetch at all, so the duplicate P3 exists to remove has not been
measured and `hook_yield` has no baseline. One batch answers both at once — the
ledger's `DUPLICATE` line and this module's `AGAINST` line — and after that,
flipping the hook stage over is an argument from evidence rather than from a
diagram.

## Four of the twelve bans stop being something an agent must remember

`docs/hook-rules.md` owns the bans; this owns the mechanical half of four.

- **#7, no third-party coverage** — `author == "third_party"`.
- **#6, no stale news as fresh** — `published_at` inside `HOOK_RECENCY_DAYS`.
- **#1, no generic site copy** — `kind == "about"` never survives, and from a
  site or a link-in-bio page only `framework` does. That is F5's narrowing: the
  verifier refutes anything that "could be sent unedited to another coach in the
  same segment", so the *cheapest* rung was producing the observations most
  likely to be refuted, and an agent walking the ladder honestly paid for that
  round trip before going to the paid rungs anyway.
- **#3, no invented specifics** — a candidate names the `obs_id` it came from,
  and its quote must actually be in that observation's text. A hook that cites a
  page nothing retrieved cannot be built here at all.

## Two rules taken from the codebase rather than invented

**No score.** `resolve.py` states it: *"Not a number — nothing in this repo
carries a numeric confidence, and one batch of 151 leads cannot calibrate a
scale."* So the ranking is a lexicographic sort key whose every component is a
named enum position, printable in words. A weighted float would look more
precise and would be a scale nobody measured.

**`unknown` is not `third_party`.** The proposal says filter to `author ==
"self"`. `AUTHORS` is three-valued, `unknown` is the dataclass default, and
`resolve.py`'s rule — *"`unknown` never means the tell said no"* — applies
verbatim one stage over. Filtering on `self` would reject most of a real pool
for lacking a field nobody was required to fill. So `third_party` is excluded
and `unknown` ranks below `self`, and authorship stays the live verifier's call.

## Where the ranking is deliberately not the ladder

`plan.LADDER` is ordered by **cost**. This is ordered by **what survives
verification**. They are different questions and F5 is the proof: retrieval has
already happened by the time this runs, so what a rung costs is a sunk fact and
the only thing left to ask is which observation is most likely to be a real hook.

## What it does not do

It writes no clause. A hook is "one or two sentences about something specific
and recent this person did, **plus a clause that says what you took from it**",
and that clause is the only genuinely authorial part of the beat. Nothing here
authors it, so nothing here emits a `HookProposal` — a proposal type whose `line`
was empty on every record would be a schema built around a gate it cannot
enforce. `Candidate` is what a ranker can honestly produce, and F4 closes when
the authorship arrives.

**And a quote found in our stored text is not a verified quote.** Every line this
module prints says "in the retrieved text" for that reason. The verifier's live
re-fetch is the only thing that has ever caught a fabricated claim, and the day
somebody reads this module's output as verification, R2 has happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date

from audit.urls import normalize as normalize_url
from outbound.lint import MIN_HOOK_WORDS, word_count
from outbound.observe import CONTENT_KINDS, KINDS, PLATFORMS, Observation, load as load_obs
from outbound.resolve import _default_of

# Owned by `docs/hook-rules.md`, which is the authority on the editorial
# judgement: would they recognise this as something they recently did? A
# different question from the 30-day activity floor, which `outbound/qualify.py`
# evaluates and `docs/spec/02-icp.md` owns. There were once four numbers here
# and the whole point of there now being two is that each has exactly one owner.
HOOK_RECENCY_DAYS = 90

# Part 7: rank mechanically, then hand a model three. Three so that a rejected
# first pick needs no second retrieval.
SHORTLIST = 3

# `Observation.days_old` is None for a record with no date AND for one whose
# date will not parse. Both sort last; without a sentinel the sort raises
# TypeError on the first evergreen framework.
UNDATED = 10_000

# Ascending, best first. Every value is a position in a named enum, never a
# weight — see the module docstring.
AUTHOR_RANK = {"self": 0, "unknown": 1}
KIND_RANK = {"post": 0, "episode": 0, "video": 1, "framework": 2, "result": 3,
             "about": 9, "bio": 9}
# Borrowed, not restated. `observe.PLATFORMS` already leads with linkedin, which
# `docs/hook-rules.md` calls "the richest source by a distance", and a second
# ordering of the same vocabulary is the drift this repo keeps finding.
PLATFORM_RANK = {name: index for index, name in enumerate(PLATFORMS)}

# Why a candidate was not offered. The name is recorded per rejection so that a
# disagreement in `--against` names the rule that caused it: a wrong rule is a
# three-line fix, and a low agreement number with no reasons is nothing anybody
# can act on.
BANS = {
    "not_content": "not a piece of content — a profile fact is not a hook",
    "site_prose": "ban #1, generic site copy — only a named framework survives "
                  "from a site, and the hero section is what the verifier "
                  "refutes as sendable to any coach in the segment",
    "third_party": "ban #7, no third-party coverage — a directory listing or an "
                   "article about them is not their voice",
    "no_date": "requirement 3, cited — a post with no date cannot be shown to "
               "be recent",
    "stale": f"ban #6, no stale news as fresh — outside {HOOK_RECENCY_DAYS} days",
    "too_short": f"under {MIN_HOOK_WORDS} words — too little to yield a quote "
                 f"and leave a clause",
}

# The five ways a verified hook can relate to what this module would have picked.
AGREEMENTS = ("agreed", "shortlisted", "missed", "unobserved", "no_pool")


@dataclass
class Candidate:
    """One observation, offered as the thing a hook could be made from."""

    lead_key: str = ""
    obs_id: str = ""          # the join proving it was retrieved, not composed
    platform: str = ""
    url: str = ""             # normalize_url'd, so a comparison is a comparison
    published_at: str = ""
    author: str = "unknown"
    kind: str = ""
    quote: str = ""           # verbatim from the observation. Never trimmed here
    words: int = 0
    rank: int = 0             # 1-based; 1 is what `select` would have picked
    why: str = ""             # the sort key in words

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Candidate":
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in data.items():
            if key not in known:
                continue
            if value is None:
                value = _default_of(known[key])
            fields[key] = value
        return cls(**fields)


@dataclass
class LeadSelection:
    """What one lead's observations offer, and what the hook stage did instead."""

    lead_key: str = ""
    name: str = ""
    shortlist: list[Candidate] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)  # {obs_id, ban, url}
    observed: int = 0                # how many observations this lead had at all
    # Every page this lead was observed on, shortlisted or not. Without it a
    # candidate that passed every ban and merely ranked fourth is indistinguish-
    # able from a page nothing ever fetched — and those two say opposite things
    # about whether the hook stage's fetch is removable.
    observed_urls: list[str] = field(default_factory=list)
    agreement: str = ""              # one of AGREEMENTS, "" when not compared
    agreement_note: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LeadSelection":
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in data.items():
            if key not in known:
                continue
            if value is None:
                value = _default_of(known[key])
            fields[key] = value
        shortlist = fields.pop("shortlist", None) or []
        selection = cls(**fields)
        selection.shortlist = [c if isinstance(c, Candidate)
                               else Candidate.from_dict(c)
                               for c in shortlist if isinstance(c, (dict, Candidate))]
        return selection

    @property
    def pick(self) -> Candidate | None:
        """What this module would have used. None is a real answer: no hook
        found is a good answer, and it is the lead holding rather than failing."""
        return self.shortlist[0] if self.shortlist else None


# ------------------------------------------------------------------ the filter


def ban_for(obs: Observation, *, today: date | None = None) -> str:
    """Which ban excludes this observation, or "" if none does.

    Ordered from the structural to the editorial, so the reason reported is the
    most fundamental one rather than whichever happened to be checked first.
    """
    today = today or date.today()

    if obs.kind not in CONTENT_KINDS:
        return "not_content"

    if obs.kind == "about":
        return "site_prose"
    if obs.platform in ("site", "linkinbio") and obs.kind != "framework":
        return "site_prose"

    if obs.author == "third_party":
        return "third_party"

    # A framework they named is evergreen, which `docs/hook-rules.md` grants
    # explicitly: "an evergreen framework or an About-page line they wrote
    # themselves is fine at any age". Everything else has to prove recency.
    if obs.kind != "framework":
        if not obs.published_at.strip():
            return "no_date"
        days = _days_old(obs, today=today)
        if days is None or days > HOOK_RECENCY_DAYS:
            return "stale"

    if word_count(obs.text) < MIN_HOOK_WORDS:
        return "too_short"
    return ""


def _days_old(obs: Observation, *, today: date | None = None) -> int | None:
    """`Observation.days_old`, against an injectable today so a test does not
    drift into failing next quarter."""
    if today is None:
        return obs.days_old
    try:
        return (today - date.fromisoformat(obs.published_at)).days
    except (TypeError, ValueError):
        return None


def sort_key(obs: Observation, *, today: date | None = None) -> tuple:
    """The ranking, as a tuple of enum positions. Ascending, best first.

    `obs_id` is last and is what makes two runs over the same pool produce
    byte-identical files — the same reason `resolve._merge` sorts on the way out.
    Length is deliberately absent: more words is not known to be better or worse,
    and inventing a direction is the calibrated-scale problem in miniature.
    """
    days = _days_old(obs, today=today)
    return (AUTHOR_RANK.get(obs.author, 9),
            KIND_RANK.get(obs.kind, 9),
            UNDATED if days is None else days,
            PLATFORM_RANK.get(obs.platform, len(PLATFORMS)),
            obs.obs_id)


def _why(obs: Observation, *, today: date | None = None) -> str:
    """The sort key in words, so a reader can see why one beat another."""
    days = _days_old(obs, today=today)
    age = f"{days}d old" if days is not None else "undated"
    return f"{obs.author} {obs.kind} on {obs.platform}, {age}"


def rank(observations: list[Observation], *, size: int = SHORTLIST,
         today: date | None = None) -> tuple[list[Candidate], list[dict]]:
    """One lead's pool, split into a ranked shortlist and the rejections.

    Returns `(shortlist, rejected)`. Both are needed: a rejection carries the
    ban that fired, which is what makes a later disagreement diagnosable.
    """
    kept, rejected = [], []
    for obs in observations:
        ban = ban_for(obs, today=today)
        if ban:
            rejected.append({"obs_id": obs.obs_id, "ban": ban,
                             "url": normalize_url(obs.url)})
        else:
            kept.append(obs)

    kept.sort(key=lambda o: sort_key(o, today=today))
    shortlist = []
    for position, obs in enumerate(kept[:max(0, size)], start=1):
        shortlist.append(Candidate(
            lead_key=obs.lead_key, obs_id=obs.obs_id, platform=obs.platform,
            url=normalize_url(obs.url), published_at=obs.published_at,
            author=obs.author, kind=obs.kind, quote=obs.text,
            words=word_count(obs.text), rank=position,
            why=_why(obs, today=today)))
    return shortlist, rejected


# --------------------------------------------------------------- the measurement


def compare(selection: LeadSelection, hook_url: str) -> tuple[str, str]:
    """How the hook stage's verified citation relates to what this would pick.

    Five verdicts, not two, and the split that matters is `missed` against
    `no_pool`. A lead whose research worker returned no observations at all tells
    you about the *corpus*; a lead whose hook came from an observation this
    module filtered out tells you about the *ranker*. Collapsing them would
    charge the ranker for somebody else's empty return, and the number that
    results is one nobody can act on.
    """
    target = normalize_url(hook_url)
    if not selection.observed:
        return "no_pool", ("the research worker returned no observations for "
                           "this lead — nothing to rank")

    for candidate in selection.shortlist:
        if candidate.url == target:
            if candidate.rank == 1:
                return "agreed", "the top pick is the page the hook cited"
            return "shortlisted", (f"the hook's page ranked {candidate.rank} of "
                                   f"{len(selection.shortlist)}")

    for rejection in selection.rejected:
        if rejection["url"] == target:
            return "missed", (f"the hook's page was observed and excluded by "
                              f"{rejection['ban']}")

    if target in selection.observed_urls:
        return "missed", (f"the hook's page survived every ban and ranked "
                          f"below the shortlist of {len(selection.shortlist)}")

    return "unobserved", ("the hook cited a page no observation carries — this "
                          "is the fetch selection could not have replaced")


def select_all(researches: list, *, size: int = SHORTLIST, hook_room: int = 0,
               against: bool = False, today: date | None = None) -> dict:
    """Every lead's selection, plus the batch report.

    **Every lead gets one**, including a lead with no observations. A selection
    is a description, not a gate — the same guarantee `resolve_all` and
    `plan_all` make.

    `researches` are research objects (or their dicts): one per lead, each
    already carrying both halves of the comparison — the observations P1 kept,
    and the hook fields the hook stage writes back.
    """
    selections = []
    for item in researches:
        data = item if isinstance(item, dict) else item.to_dict()
        observations = load_obs(data.get("observations") or [])
        lead_key = next((o.lead_key for o in observations if o.lead_key), "") \
            or (data.get("email") or "").strip().lower() \
            or (data.get("slug") or "")

        shortlist, rejected = rank(observations, size=size, today=today)
        selection = LeadSelection(
            lead_key=lead_key, name=data.get("name") or "",
            shortlist=shortlist, rejected=rejected,
            observed=len(observations),
            observed_urls=sorted({normalize_url(o.url) for o in observations}))

        if not observations:
            selection.notes.append(
                "no observations — nothing to rank, which is a fact about the "
                "research return rather than about this lead")
        elif not shortlist:
            selection.notes.append(
                "every observation was excluded — no hook found is a good "
                "answer, and the lead holds rather than failing")

        # Advisory only, and only when the caller passes it. `deal` runs before
        # the hook stage now (F11), so the room is knowable — but it is a
        # per-batch number handed in, never derived here. MIN_HOOK_WORDS is a
        # FLOOR on the hook, not a ceiling, and reusing it as the room would be
        # one number wearing two meanings in two stages, which is the drift that
        # gave this stage four recency windows.
        if hook_room and selection.pick and selection.pick.words > hook_room * 6:
            selection.notes.append(
                f"TIGHT: the top pick is {selection.pick.words} words against "
                f"{hook_room} of room — a fair contraction, which is what the "
                f"verifier allows, may not reach that far")

        if against:
            if (data.get("hook_verified") or "") == "verified" \
                    and (data.get("hook_source_url") or "").strip():
                selection.agreement, selection.agreement_note = compare(
                    selection, data["hook_source_url"])
        selections.append(selection)

    return {"selections": selections,
            "report": report(selections, hook_room=hook_room, against=against)}


# ------------------------------------------------------------------- the gate


def validate(selection: LeadSelection) -> list[str]:
    """Schema violations. An empty list means the record is a real one."""
    problems: list[str] = []

    if not selection.lead_key.strip():
        problems.append("no lead_key — without it nothing joins this selection "
                        "to a lead, an observation or a ledger line")
    if selection.agreement and selection.agreement not in AGREEMENTS:
        problems.append(f"agreement={selection.agreement!r} is not one of "
                        f"{AGREEMENTS}")

    ranks = []
    for index, candidate in enumerate(selection.shortlist):
        where = f"candidate[{index}]"
        if not candidate.obs_id.strip():
            problems.append(f"{where} names no obs_id — the join is what proves "
                            f"a hook came from something retrieved rather than "
                            f"something composed")
        if candidate.platform not in PLATFORMS:
            problems.append(f"{where} platform={candidate.platform!r} is not "
                            f"one of {PLATFORMS}")
        if candidate.kind not in KINDS:
            problems.append(f"{where} kind={candidate.kind!r} is not one of "
                            f"{KINDS}")
        if not candidate.url.strip():
            problems.append(f"{where} has no url — a candidate names the page "
                            f"it came from")
        if not candidate.quote.strip():
            problems.append(f"{where} quotes nothing — a candidate that quotes "
                            f"nothing was reasoned, not fetched")
        ranks.append(candidate.rank)

    if ranks and sorted(ranks) != list(range(1, len(ranks) + 1)):
        problems.append(f"ranks are {ranks}, which is not 1..{len(ranks)} — a "
                        f"reader cannot tell which one would have been used")
    return problems


def validate_all(selections: list[LeadSelection]) -> list[str]:
    """Every selection's problems, each prefixed with which one it was."""
    problems = []
    for index, selection in enumerate(selections):
        for problem in validate(selection):
            problems.append(f"selection[{index}] {problem}")
    return problems


def load(data) -> list[LeadSelection]:
    """One selection or a list of them, as `plan` accepts one or many."""
    rows = data if isinstance(data, list) else [data]
    if isinstance(data, dict) and "selections" in data:
        rows = data["selections"]
    return [LeadSelection.from_dict(row) for row in rows if isinstance(row, dict)]


def schema_help() -> str:
    """The field list, generated from the dataclasses rather than written down."""
    from dataclasses import fields as dataclass_fields

    rows = [f"    {f.name:20} {getattr(f.type, '__name__', str(f.type))}"
            for f in dataclass_fields(LeadSelection)]
    candidate_rows = [f"      {f.name:18} {getattr(f.type, '__name__', str(f.type))}"
                      for f in dataclass_fields(Candidate)]
    return ("  selections, one per lead:\n" + "\n".join(rows)
            + "\n    each candidate:\n" + "\n".join(candidate_rows)
            + f"\n  agreement is one of {AGREEMENTS}\n"
              f"  rank is 1-based and 1 is what select would have used\n"
              "  quote is the observation's text VERBATIM. It is not a verified "
              "quote:\n  it is in the text we stored, which is a different "
              "claim from being on the page.")


def report(selections: list[LeadSelection], *, hook_room: int = 0,
           against: bool = False) -> str:
    """The quotable summary, in the shape `resolve.report` already uses."""
    problems = validate_all(selections)
    head = "VALID" if not problems else f"INVALID ({len(problems)})"
    observed = sum(s.observed for s in selections)
    with_pool = [s for s in selections if s.observed]
    picked = [s for s in selections if s.pick]

    by_ban: dict[str, int] = {}
    for selection in selections:
        for rejection in selection.rejected:
            by_ban[rejection["ban"]] = by_ban.get(rejection["ban"], 0) + 1
    bans = ", ".join(f"{n} {name}" for name, n in sorted(by_ban.items())) or "none"

    lines = [
        f"SELECT: {head}, {len(selections)} lead(s), {observed} observation(s) "
        f"over {len(with_pool)} lead(s) with a pool",
        f"  {len(picked)} lead(s) have a candidate, "
        f"{len(with_pool) - len(picked)} had a pool and nothing survived",
        f"  excluded: {bans}",
    ]

    if against:
        compared = [s for s in selections if s.agreement]
        counts = {name: sum(1 for s in compared if s.agreement == name)
                  for name in AGREEMENTS}
        lines.append(
            f"  AGAINST: {len(compared)} verified hook(s) — "
            + ", ".join(f"{counts[name]} {name}" for name in AGREEMENTS))
        for selection in compared:
            if selection.agreement in ("missed", "unobserved"):
                lines.append(f"  {selection.agreement.upper():10} "
                             f"{selection.lead_key or selection.name} — "
                             f"{selection.agreement_note}")

    if hook_room:
        lines.append(f"  hook room {hook_room} words, advisory only")
    else:
        lines.append("  hook room not given — pass --hook-room with the LOW end "
                     "of the `hook room <lo> to <hi> words` range `deal` prints "
                     "before this stage now (F11). Without it length is a floor "
                     "on the observation and nothing else")

    for problem in problems:
        lines.append(f"  SCHEMA  {problem}")
    if problems:
        lines.append(schema_help())
    lines.append("  ADVISORY. Nothing here writes a hook, nothing reads this "
                 "file, and a quote found here is in the text we stored — not "
                 "verified on the page. That is still the verifier's live fetch.")
    return "\n".join(lines)
