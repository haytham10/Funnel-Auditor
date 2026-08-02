"""Which observation the hook is made from, chosen without fetching anything.

The hook stage used to be the one consequential stage that searched.
`hook-worker` opened a context per lead, walked a ladder written in prose, and
fetched — after `research-worker` had already fetched, for the same lead, and
thrown the material away (F1, F2). This module is the other half of that: a
ranking over the observations research kept, so that finding a hook is selection
rather than search.

**This runs BEFORE the hook stage and the hook stage consumes it** (2026-08-01,
D27). It hands each lead a shortlist of three candidates carrying their
observations' verbatim text; `hook-worker` picks one, quotes it and writes the
clause. The ranking is the whole of what a machine can honestly decide here —
recency, authorship, kind, length against the room — and the clause is the whole
of what it cannot.

**Three so that a rejected first pick needs no second retrieval.** That is the
number's only justification and it is worth keeping in view: the shortlist is
sized to make the escalation rare, not to give the model a menu.

## What it still refuses to be

**It verifies nothing, and the flip makes that matter more rather than less.**
A quote found here is in the text *we stored*, put there by a different agent at
a different hour. Whether those words are on the page is `hook-verifier`'s
question and it answers it with a live re-fetch. That fetch is not overhead; it
is the only mechanism in this system that has ever caught a fabricated claim,
and reading this module's output as verification is exactly how it would be
retired (R2).

**And it does not decide who gets drafted.** A lead whose every observation is
banned gets no candidate, which means a null hook — a good answer, and the lead
holds rather than failing.

## `--against` survives the flip, and now means something more useful

It compared the ranker's pick to the hook the stage had already paid to find.
Post-flip the hook comes from the shortlist, so the same five verdicts read as
what the worker did with it:

- **agreed** — it took rank 1.
- **shortlisted** — it took rank 2 or 3, which is the shortlist earning its size.
- **missed** — it used an observation this module banned. A ban to re-examine.
- **unobserved** — **it escalated.** This is the escalation rate, and it is the
  number that says whether the flip holds.
- **no_pool** — research returned nothing for that lead. A fact about the
  corpus, not about the ranker.

## Four of the twelve bans stop being something an agent must remember

`docs/hook-rules.md` owns the bans; this owns the mechanical half of four.

- **#7, no third-party coverage** — `author == "third_party"`.
- **#6, no stale news as fresh** — `published_at` inside `HOOK_RECENCY_DAYS`.
- **#1, no generic site copy** — the same text observed for two different leads.
  A sentence that appears on two coaches' pages is, by definition, one that
  could be sent unedited to another coach in the segment; that is the verifier's
  own test, made mechanical against the only evidence that can settle it.
- **#3, no invented specifics** — a candidate names the `obs_id` it came from,
  and its quote must actually be in that observation's text. A hook that cites a
  page nothing retrieved cannot be built here at all.

## Ban #1 was location, and location was the wrong proxy (2026-08-01)

F5's narrowing made ban #1 mean `kind == "about"`, plus "from a site or a
link-in-bio page only `framework` survives". Batch `2026-08-01-q1` refuted it
with evidence rather than argument: **all three MISSED leads were `kind: about`
observations that an independent verifier had VERIFIED** — Rory Buck's race
result, Sanaa Diab's named client project, Bindu Joseph's career pivot. One ban
accounted for 100% of the ranker's misses and for 21 of the 32 rejections in the
whole corpus.

What the verifier refuses is the **generic**, not the location. A person's own
About page is where a solo coach writes the most specific thing they will ever
publish, and the recency exemption `docs/hook-rules.md` already granted in prose
— *"an evergreen framework or an About-page line they wrote themselves is fine
at any age"* — had been narrowed away in code, so removing the location ban
alone would have moved those three from `site_prose` to `no_date` and changed
nothing.

So the location ban is gone, `about` carries the same date exemption as
`framework`, and `KIND_RANK` does the work the ban was doing badly: an About
page ranks last and is offered only when the lead has nothing better. The
mechanical half of ban #1 is now `boilerplate`, above, which fires on evidence
that a line is generic rather than on where it was found.

## The half-day this was banned outright, and why that was wrong (2026-08-02)

`2026-08-02-q2` produced a real contradiction and one wrong reading of it.

The measurement: of 42 observations, **26 were `about` and none carried a date**.
Ten of fourteen leads with a shortlist were offered nothing else, and two hook
workers — independently, on different leads — **wrote today's date for a page
that has none**, one citing the other's file as precedent.

The wrong reading was that About pages should stop being shortlisted. They were
banned by kind for about an hour. That is the wrong end of the pipe: the ranker
was doing its job, offering a weak fallback last, exactly as designed.

**The contradiction lived in `outbound/hook.py`, which required a non-empty
`published_at` from every proposal and exempted no kind.** So a worker handed a
legitimate undated About page had two moves: abandon the hook, or invent a date.
Two took the second. Deleting the fallback removes the symptom and the fallback;
fixing the gate removes the impossible instruction.

So `hook` now accepts an empty `published_at` when the observation it cites is
evergreen and genuinely carries none — and, with `--against`, **rejects a
non-empty date on a source that has none**, which is the fabrication itself made
mechanical. This module is unchanged: an About page is a valid hook, ranked
last, offered when nothing recent survives.

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
enforce. `Candidate` is what a ranker can honestly produce; `hook-worker` turns
one into a proposal and `outbound/hook.py` gates it.

**The join back is what makes ban #3 mechanical.** A proposal names the `obs_id`
it came from, and `hook --against` checks the quote really is a contiguous piece
of that candidate's text. "No invented specifics" was a sentence an agent was
asked to remember for as long as there was nothing to check it against. There
is now.
"""

from __future__ import annotations

import re
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

# Exempt from both date rules, per `docs/hook-rules.md`. `about` is here because
# a page somebody wrote about themselves has no publication date and never will,
# and requiring one is a way of banning the kind while appearing not to. It
# still ranks last in `KIND_RANK`: exempt from the date, never preferred — an
# About page is what a lead gets offered when nothing recent survives, which is
# exactly the job it should do.
#
# This exemption was briefly removed on 2026-08-02 and put straight back. See
# the docstring section below: the contradiction it was blamed for lived in
# `outbound/hook.py`, not here, and deleting the fallback was the wrong end to
# fix it from.
EVERGREEN_KINDS = ("framework", "about")
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
    "boilerplate": "ban #1, generic site copy — this exact text was observed for "
                   "another lead too, which is the verifier's own test (could it "
                   "be sent unedited to another coach) settled on evidence",
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


_PUNCT = re.compile(r"[^a-z0-9 ]+")


def fingerprint(text: str) -> str:
    """One observation's text, reduced so that two copies of it compare equal.

    Case, punctuation and whitespace only. Nothing semantic: two pages that say
    the same thing in different words are a judgement, and this is the half that
    can be settled without one.
    """
    return _PUNCT.sub(" ", (text or "").lower()).strip()


def boilerplate_of(pairs: list) -> frozenset:
    """Texts observed for more than one lead — the batch's generic copy.

    `pairs` is `[(lead_key, text), ...]`. The key is passed in rather than read
    off the observation because `select_all` derives it from the research object
    when the worker left it blank, and two blank keys must not be read as one
    lead agreeing with itself.

    Whole text, not per sentence. A sentence-level version fires on "Book a free
    discovery call" and would ban the page that happens to carry it alongside
    the one specific thing the lead ever wrote; this fires only when two leads'
    pages are the *same page's worth of words*, which is template chrome and
    nothing else.

    Two distinct leads, not two records: one lead's own text retrieved twice is
    a duplicate fetch, which is the ledger's business and not a reason to ban
    their only observation.
    """
    leads: dict[str, set] = {}
    for lead_key, text in pairs:
        mark = fingerprint(text)
        # An observation nobody could attribute takes no part. Grouping every
        # keyless record under "" would let two of them convict each other, and
        # counting each as its own lead would do the same thing faster. The
        # asymmetry decides it: a ban is a lead losing its only observation, so
        # unknown attribution abstains.
        if mark and lead_key:
            leads.setdefault(mark, set()).add(lead_key)
    return frozenset(mark for mark, keys in leads.items() if len(keys) > 1)


def ban_for(obs: Observation, *, today: date | None = None,
            boilerplate: frozenset | set = frozenset()) -> str:
    """Which ban excludes this observation, or "" if none does.

    Ordered from the structural to the editorial, so the reason reported is the
    most fundamental one rather than whichever happened to be checked first.

    `boilerplate` is the batch's repeated-text set from `boilerplate_of`. It is
    empty by default, so a single observation judged on its own is judged on
    what it is — the generic test needs a corpus and honestly says so rather
    than guessing from one record.
    """
    today = today or date.today()

    if obs.kind not in CONTENT_KINDS:
        return "not_content"

    if fingerprint(obs.text) in boilerplate:
        return "boilerplate"

    if obs.author == "third_party":
        return "third_party"

    # Evergreen, and `docs/hook-rules.md` grants both halves: "an evergreen
    # framework OR an About-page line they wrote themselves is fine at any age".
    # The code carried only the first half until 2026-08-01, which is why three
    # verified About-page hooks were excluded — first as `site_prose`, and then,
    # when that ban went, as `no_date`. Everything else has to prove recency.
    if obs.kind not in EVERGREEN_KINDS:
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
         today: date | None = None,
         boilerplate: frozenset | set = frozenset(),
         ) -> tuple[list[Candidate], list[dict]]:
    """One lead's pool, split into a ranked shortlist and the rejections.

    Returns `(shortlist, rejected)`. Both are needed: a rejection carries the
    ban that fired, which is what makes a later disagreement diagnosable.

    `boilerplate` comes from the whole batch and is computed once by
    `select_all`, because the generic test is a comparison between leads and one
    lead's pool cannot answer it.
    """
    kept, rejected = [], []
    for obs in observations:
        ban = ban_for(obs, today=today, boilerplate=boilerplate)
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
    rows = [item if isinstance(item, dict) else item.to_dict()
            for item in researches]
    pools = [load_obs(data.get("observations") or []) for data in rows]
    keys = [next((o.lead_key for o in pool if o.lead_key), "")
            or (data.get("email") or "").strip().lower()
            or (data.get("slug") or "")
            for data, pool in zip(rows, pools)]
    # Ban #1's mechanical half, and it needs every lead's pool at once. Computed
    # here rather than in `rank` so that one lead's page cannot be called generic
    # on the strength of that same lead's other page.
    boilerplate = boilerplate_of([(key, obs.text)
                                  for key, pool in zip(keys, pools)
                                  for obs in pool])

    selections = []
    for data, observations, lead_key in zip(rows, pools, keys):
        shortlist, rejected = rank(observations, size=size, today=today,
                                   boilerplate=boilerplate)
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
        # The word means the opposite thing it used to and the same line prints
        # it, so the reading is stated rather than assumed. Before the flip an
        # unobserved hook was a fetch selection could not have replaced; now it
        # is a fetch selection did not manage to avoid.
        lines.append(f"  {counts['unobserved']} of {len(compared)} escalated "
                     f"— UNOBSERVED post-flip is the escalation rate, not a "
                     f"fetch this stage could not have replaced")

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
    lines.append("  The hook stage reads this file. Nothing here writes a hook "
                 "or verifies one: a quote found here is in the text WE STORED, "
                 "and whether those words are on the page is the verifier's "
                 "live re-fetch, which is unchanged and matters more now.")
    return "\n".join(lines)
