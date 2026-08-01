"""Which channels are plausibly this lead's own, and on what evidence.

**About 40 of 151 rows on the first real batch pointed at the wrong person** —
parked domains, name collisions, a coach's training school, an Ohio retreat
house, a Dutch tech-news site. That is F7 of
docs/proposals/2026-08-01-hook-retrieval.md, and the reason it cost what it did
is not that nothing checked. Three things checked:

    handle contains the name?   normalize._profile_name_notes   -> a note
    site mentions the name?     fetch.check_owner               -> a report line
    is this really them?        each agent, improvised          -> by hand

Every one is advisory prose that no data structure carries forward, so every bad
row was found by a worker, one at a time, **after** the money was spent. This
module is the same two free checks with a type on them.

**Advisory, never a kill — and never a non-zero exit.** Being advisory is the
right call for dropping a lead: a false kill is permanent and invisible. It is
the wrong call for a *purchase*, and that is the distinction this stage exists
to make. In P3 `plan` will decline to buy a LinkedIn scrape for a channel whose
ownership is `absent`. Nothing here declines anything, and a run where every
channel is `absent` exits 0. That is R3 of the proposal, and exit 1 is the
natural mistake.

**Nothing consumes an Identity yet**, the same posture the ledger and the
observation contract shipped in. What lands is the contract and the rule set, so
that when `plan` arrives it reads verdicts that were checked at the moment they
were written rather than prose reassembled later.

## Why this runs after `fetch` and not before it

Part 5's diagram puts `resolve` first. That diagram has no `fetch` stage at all
— tier 0 has been absorbed into `observe` by then, which is P3. Read as a P2
instruction it imports an ordering whose precondition has not shipped: in the
machine as it stands, a resolve-before-fetch would have to read each homepage to
harvest socials and `fetch` would read it again seconds later. That is one
duplicate `(lead_key, url)` per lead with a site — 89 of 151 on the first batch
— and `ledger.duplicates` would name every one, burying the single
`DUPLICATE li_posts` line P0 exists to expose. A signal people are trained to
scroll past is worse than no signal.

So the only thing this module fetches is the link-in-bio page, which nothing
fetches today (F8). `resolve_lead` takes its site read as an argument and its
fetcher by injection, so when tier 0 moves into `observe` the caller changes and
none of the logic does.

## The three properties that make the verdicts auditable

- **`unknown` is never "the tell said no."** It is "no tell was available."
  Rule 4 below is the only path to `absent`. Without this, every opaque channel
  id — `youtube.com/channel/UC1a2b3c` folds to `ucabc` — reads as a name
  mismatch, the report fills with false negatives, and people learn to ignore
  the line. That is exactly the failure that made the existing OWNER-CHECK worth
  building, reintroduced one layer down.
- **Provenance only promotes, never demotes.** A channel is never downgraded for
  where it was found. Otherwise a coach whose site carries only a brand name
  drags every real channel they have to `absent`.
- **Rule 3 leans toward `confirmed` on purpose.** A page that names them can
  still link somebody else's channel — a podcast they guested on, a partner's
  Instagram. In P3 this gates spend, so a false `confirmed` costs one scrape and
  a false `absent` costs a channel. That is the machine's own asymmetry, pointed
  at retrieval instead of the floors. `evidence` names the page rather than
  asserting the fact, so the reader can see which it is.
"""

from __future__ import annotations

import re
from dataclasses import MISSING, dataclass, field, asdict
from urllib.parse import urlparse

from audit.email_check import name_tokens
from audit.urls import normalize as normalize_url
from outbound.observe import PLATFORMS

# `check_owner`'s three words, one layer down: per channel instead of per site.
# Not a number — nothing in this repo carries a numeric confidence, and one
# batch of 151 leads cannot calibrate a scale.
CONFIDENCE = ("confirmed", "absent", "unknown")

# Where the URL was discovered. `row` is the intake CSV, `site` is the tier-0
# harvest, `linkinbio` is a page this module read itself.
SOURCES = ("row", "site", "linkinbio")

# `check_owner` uses min_len=3 so a single initial cannot match everything. A
# handle shorter than this after folding is not something to judge a person on.
MIN_HANDLE_LETTERS = 3

# A LinkedIn company page is not a person. `li_posts` takes a profile URL, so
# this is a routing fact as much as an ownership one.
_LINKEDIN_COMPANY = re.compile(r"^/company/", re.I)

# Path segments that carry no name even when they carry characters. Every one of
# these folds to something a token test would call a mismatch.
_OPAQUE_SEGMENTS = re.compile(
    r"^(uc[\w\-]{10,}|profile\.php|pages|people|show|episode|podcast|id\d+)$",
    re.I)


def _default_of(dataclass_field):
    """A field's default, whether it is a value or a factory.

    `Observation.from_dict` reads `.default` directly because none of its fields
    is a list. Half of these are, and `.default` on a `default_factory` field is
    `MISSING` — which is not `None`, so it sails through the coercion and blows
    up as a TypeError on the first `null` a worker writes.
    """
    if dataclass_field.default is not MISSING:
        return dataclass_field.default
    if dataclass_field.default_factory is not MISSING:
        return dataclass_field.default_factory()
    return None


@dataclass
class Channel:
    """One place this lead might be reachable, and how sure we are it is them."""

    platform: str = ""           # one of observe.PLATFORMS
    url: str = ""                # normalize_url'd — the canonical form
    handle: str = ""             # the folded handle the rules ran on; "" = nothing checkable
    confidence: str = "unknown"  # confirmed | absent | unknown
    evidence: str = ""           # which rule fired, in words
    source: str = "row"          # row | site | linkinbio

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Channel":
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
class Identity:
    """Everything free retrieval can say about who a row is actually about."""

    lead_key: str = ""           # fetch.lead_key — joins to sites.json AND the ledger
    name: str = ""
    slug: str = ""
    channels: list[Channel] = field(default_factory=list)
    # A PASS-THROUGH of `fetch.check_owner` on their OWN site, never re-derived
    # from the channels. It answers "does their site name them", which is a
    # different question from "is this Instagram theirs", and one word with two
    # meanings across two files is how docs/spec/06-state.md's failure starts.
    owner_verdict: str = "unknown"
    notes: list[str] = field(default_factory=list)
    # Link-in-bio pages THIS module fetched. Once retrieve-once holds, nothing
    # will read that page again — reducing it to a channel list and dropping the
    # body would commit F2 fresh in the stage written to end it.
    observations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Identity":
        """Build from JSON, dropping unknown keys and coercing `null` to the
        field default — the same coercion `Observation.from_dict` does."""
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in data.items():
            if key not in known:
                continue
            if value is None:
                value = _default_of(known[key])
            fields[key] = value
        channels = fields.pop("channels", None) or []
        identity = cls(**fields)
        identity.channels = [
            c if isinstance(c, Channel) else Channel.from_dict(c)
            for c in channels if isinstance(c, (dict, Channel))]
        return identity

    @property
    def has_confirmed_channel(self) -> bool:
        """Is there anything here we are sure about? Deliberately separate from
        `owner_verdict`, which is only ever about their own site."""
        return any(c.confidence == "confirmed" for c in self.channels)


# ------------------------------------------------------------------- handles


def handle_of(url: str, platform: str = "") -> str:
    """The part of a profile URL that could carry a name, or "" if none does.

    **Three-valued through the empty string, and that is the whole point.** The
    note version of this check did `re.sub(r"[^a-z]+", "", url.rsplit("/",1)[-1]
    .lower())`, which turns `youtube.com/channel/UC1a2b3c` into `ucabc` and then
    reports that it does not contain the lead's name. That is harmless only
    because it never looked at YouTube. Extended to every platform without a
    guard, every opaque id becomes a false `absent`.

    So an id that cannot carry a name returns "", and "" routes to `unknown`.
    """
    try:
        parsed = urlparse(url if "//" in url else "//" + url)
    except ValueError:
        return ""
    segments = [s for s in parsed.path.split("/") if s]
    if not segments:
        return ""

    if platform == "linkedin":
        # /in/<slug> is a person; /company/<slug> was already turned away.
        if segments[0].lower() != "in" or len(segments) < 2:
            return ""
        candidate = segments[1]
    elif platform == "youtube":
        # Only the @handle and /c/<name> forms carry a name. /channel/UC… is an
        # opaque id, and /user/<name> is legacy but still a name.
        first = segments[0]
        if first.startswith("@"):
            candidate = first
        elif first.lower() in ("c", "user") and len(segments) > 1:
            candidate = segments[1]
        else:
            return ""
    elif platform == "podcast":
        # A show id is a hash and a show *name* is not a person's name. Rule 3
        # is the only honest way to attribute a podcast.
        return ""
    else:
        candidate = segments[0]

    if _OPAQUE_SEGMENTS.match(candidate):
        return ""
    folded = re.sub(r"[^a-z]+", "", candidate.lower())
    return folded if len(folded) >= MIN_HANDLE_LETTERS else ""


def handle_matches(handle: str, tokens: list[str]) -> bool:
    """Does a folded handle carry any part of the name? The same containment
    test `check_owner` runs over page text, on a shorter haystack."""
    return bool(handle) and any(token in handle for token in tokens)


def score_channel(url: str, platform: str, tokens: list[str], *,
                  source: str = "row", from_page: str = "",
                  page_owner: str = "unknown") -> tuple[str, str, str]:
    """One channel's `(handle, confidence, evidence)`, by the rules in order.

    `page_owner` is the ownership verdict of the page this URL was harvested
    from — `SiteRead.owner_match` for a site, or the link-in-bio page's own
    verdict. It can only promote (rule 3); there is no rule that demotes on it.
    """
    # 0 — structurally not a person. Checked before the name, because a company
    #     slug can contain the coach's name and still not be a profile.
    if platform == "linkedin":
        path = urlparse(url if "//" in url else "//" + url).path
        if _LINKEDIN_COMPANY.match(path):
            return "", "unknown", ("linkedin company page, not a person — "
                                   "li_posts takes a profile URL")

    handle = handle_of(url, platform)

    # 1 — nothing to check against. Not the lead's fault and not a verdict.
    if not tokens:
        return handle, "unknown", "no name on the row to check against"

    # 2 — the handle says so.
    if handle_matches(handle, tokens):
        matched = next(t for t in tokens if t in handle)
        return handle, "confirmed", f"handle {handle!r} contains {matched!r}"

    # 3 — the page it was linked from says so. Promotes only.
    if page_owner == "confirmed" and from_page:
        return handle, "confirmed", f"linked from {from_page}, which names them"

    # 4 — the only path to `absent`: a tell was available and it said no.
    if handle:
        return handle, "absent", (f"handle {handle!r} contains no part of "
                                  f"their name")

    # 5 — no tell was available.
    return handle, "unknown", "channel id carries no name to check"


# ------------------------------------------------------------------ resolving


def _platform_of(url: str) -> str:
    """The platform label `normalize` already assigns, reused rather than
    copied: PLATFORM_HOSTS is the authority on which host is which."""
    from outbound.normalize import classify_site

    verdict = classify_site(url)
    if verdict.verdict == "platform" and verdict.platform in PLATFORMS:
        return verdict.platform
    return ""


def _merge(channels: list[Channel]) -> list[Channel]:
    """One entry per canonical URL, keeping the strongest verdict.

    Strongest wins rather than first-seen, so the order leads happen to arrive
    in cannot change a verdict. Sorted on the way out so two runs over the same
    input produce byte-identical files — this one is meant to be diffed against
    the last batch's.
    """
    rank = {"confirmed": 0, "absent": 1, "unknown": 2}
    best: dict[str, Channel] = {}
    for channel in channels:
        existing = best.get(channel.url)
        if existing is None or rank[channel.confidence] < rank[existing.confidence]:
            best[channel.url] = channel
    order = {name: i for i, name in enumerate(PLATFORMS)}
    return sorted(best.values(),
                  key=lambda c: (order.get(c.platform, len(PLATFORMS)), c.url))


def _linkinbio_urls(lead) -> list[str]:
    """The link-in-bio pages on this row. Already discovered, never fetched.

    `normalize` has routed linktr.ee, beacons.ai, stan.store, bio.link,
    milkshake.app and taplink.cc into `other_urls` since intake was written,
    with a comment recording that dropping them was a real bug. And then
    `batch_fetch` targets `site_url` and nothing else, so no stage has ever read
    one. That is F8: a linktree is a free HTTP page listing every channel a
    coach has — the cheapest identity artifact available, discovered and
    discarded.
    """
    urls = []
    for url in (getattr(lead, "other_urls", None) or []):
        if _platform_of(url) == "linkinbio":
            urls.append(normalize_url(url))
    return list(dict.fromkeys(urls))


def _read_linkinbio(lead_key_value: str, url: str, tokens: list[str],
                    fetch_page) -> tuple[list[tuple[str, str]], str, dict, str]:
    """Read one link-in-bio page: its channels, its own ownership, its record.

    Returns `(channels, page_owner, observation, note)`. A page that will not
    load yields a note and empties, never a raise — the same posture
    `fetch.get_page` takes, and for the same reason: this stage cannot be
    allowed to take a batch down over a linktree.
    """
    from outbound import ledger

    page = fetch_page(url)
    ledger.record(lead_key=lead_key_value, stage="resolve", platform="linkinbio",
                  url=url, retrieved_by="tier0", cost_usd=0.0, secs=page.secs,
                  outcome=page.outcome, purpose="observe")

    if not page.html:
        return [], "unknown", {}, (f"link-in-bio page unreadable ({url}): "
                                   f"{page.error or page.status}")

    # Does the page itself name them? Only then can it vouch for what it links.
    # The handle is checked as well as the text, because a linktree is often a
    # wall of buttons with almost no prose on it.
    haystack = f"{page.text} {url}".lower()
    page_owner = "unknown"
    if tokens:
        page_owner = "confirmed" if any(t in haystack for t in tokens) else "unknown"

    channels = []
    for platform, pattern in _social_patterns().items():
        for match in pattern.finditer(page.html):
            channels.append((platform, normalize_url(match.group(0))))

    # Kept verbatim. Once retrieve-once holds nothing reads this page again, and
    # reducing it to a list of links would be F2 committed fresh by the stage
    # written to end it. `bio` is not a CONTENT_KIND, so a wall of buttons with
    # no prose still validates.
    from datetime import datetime, timezone

    observation = {
        "lead_key": lead_key_value,
        "platform": "linkinbio",
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "author": "self" if page_owner == "confirmed" else "unknown",
        "kind": "bio",
        "text": page.text,
        "cost_usd": 0.0,
        "retrieved_by": "tier0",
    }
    return channels, page_owner, observation, ""


def _social_patterns():
    """`fetch`'s harvest patterns, borrowed rather than restated. They are one
    definition of what a profile URL looks like, and the pixel they used to
    match is the reason a second copy is not wanted."""
    from outbound.fetch import _SOCIAL_RE

    return _SOCIAL_RE


def resolve_lead(lead, read=None, *, fetch_page=None) -> Identity:
    """One lead's Identity, from its row plus whatever tier 0 already read.

    Pure but for `fetch_page`, which is injected rather than imported so the
    tests stub HTTP without touching module globals and so P3's re-ordering is a
    caller change. Passing `fetch_page=None` means no link-in-bio page is read
    and the channels come from the row and the site harvest alone.
    """
    from outbound.fetch import lead_key as _lead_key

    identity = Identity(
        lead_key=_lead_key(lead),
        name=getattr(lead, "name", "") or "",
        slug=getattr(lead, "slug", "") or "",
        owner_verdict=getattr(read, "owner_match", "unknown") if read else "unknown",
    )
    tokens = name_tokens(identity.name, min_len=MIN_HANDLE_LETTERS)
    site_url = getattr(lead, "site_url", "") or ""
    site_host = urlparse(site_url).netloc if site_url else ""

    candidates: list[tuple[str, str, str, str]] = []   # url, platform, source, from_page

    # The row's own columns.
    for url in (lead.social_urls() if hasattr(lead, "social_urls") else []):
        platform = _platform_of(url)
        if platform:
            candidates.append((url, platform, "row", ""))

    # What tier 0 harvested off their site. `from_page` is the site, so a site
    # that names them can promote the channels it links.
    for platform, url in (getattr(read, "social", {}) or {}).items():
        if platform in PLATFORMS:
            candidates.append((url, platform, "site", site_host))

    # The link-in-bio page, which is the only thing this stage fetches. It is
    # listed on the row already and no stage has ever read it (F8), and a page
    # that names the coach vouches for every channel it lists — the cheapest
    # attribution available anywhere in this machine.
    for url in _linkinbio_urls(lead):
        candidates.append((url, "linkinbio", "row", ""))
        if fetch_page is None:
            continue
        found, page_owner, observation, note = _read_linkinbio(
            identity.lead_key, url, tokens, fetch_page)
        if note:
            identity.notes.append(note)
        if observation:
            identity.observations.append(observation)
        host = urlparse(url).netloc
        for platform, linked in found:
            if platform in PLATFORMS:
                candidates.append((linked, platform, "linkinbio",
                                   host if page_owner == "confirmed" else ""))

    channels = []
    for url, platform, source, from_page in candidates:
        canonical = normalize_url(url)
        # A `from_page` is only ever set by a source that has already decided
        # the page names them: the site read carries its own owner verdict, and
        # a link-in-bio page is checked when it is read.
        page_owner = "unknown"
        if source == "site":
            page_owner = identity.owner_verdict
        elif source == "linkinbio" and from_page:
            page_owner = "confirmed"
        handle, confidence, evidence = score_channel(
            canonical, platform, tokens, source=source, from_page=from_page,
            page_owner=page_owner)
        channels.append(Channel(platform=platform, url=canonical, handle=handle,
                                confidence=confidence, evidence=evidence,
                                source=source))

    identity.channels = _merge(channels)

    if not identity.channels:
        identity.notes.append(
            "no channel found on the row or the site read — free retrieval "
            "has nothing to offer this lead, which is a fact worth having "
            "rather than a gap each worker rediscovers")
    return identity


def resolve_all(leads: list, reads: dict | None = None, *,
                fetch_page=None, workers: int = 0) -> dict:
    """Every lead's Identity, plus the batch report.

    **Every lead gets one**, including a lead with no channels and a lead whose
    every channel is `absent`. An Identity is a description, not a gate.

    Concurrent when it fetches, serial when it does not. `batch_fetch`'s
    docstring records why: 151 sites at a 15-second timeout blew through a
    120-second ceiling and then a 590-second one, and was killed twice before
    finishing. Nobody in this module should write a new serial network loop.
    Results are collected into a list in input order, so completion order does
    not leak into the file.
    """
    from concurrent.futures import ThreadPoolExecutor

    from outbound.fetch import DEFAULT_WORKERS, lead_key as _lead_key

    reads = reads or {}
    if fetch_page is None:
        identities = [resolve_lead(lead, reads.get(_lead_key(lead)))
                      for lead in leads]
    else:
        def one(lead):
            return resolve_lead(lead, reads.get(_lead_key(lead)),
                                fetch_page=fetch_page)

        pool_size = max(1, min(workers or DEFAULT_WORKERS, len(leads) or 1))
        with ThreadPoolExecutor(max_workers=pool_size) as pool:
            identities = list(pool.map(one, leads))
    return {"identities": identities, "report": report(identities)}


def page_reader():
    """The default link-in-bio fetcher: `fetch.get_page` on a per-thread
    session. Built here rather than defaulted in the signature so that "did
    anything touch the network" stays a property of the call, not of a global."""
    from outbound.fetch import get_page, _thread_session

    return lambda url: get_page(url, _thread_session())


# ------------------------------------------------------------------- the gate


def validate(identity: Identity) -> list[str]:
    """Schema violations. An empty list means the record is a real one.

    The interesting one is a `confirmed` or `absent` with no evidence: that is
    `research`'s rule — a hard verdict naming no source was reasoned rather than
    fetched — applied to ownership.
    """
    problems: list[str] = []

    if not identity.lead_key.strip():
        problems.append("no lead_key — without it nothing joins this to a lead, "
                        "a site read or a ledger line")
    if identity.owner_verdict not in CONFIDENCE:
        problems.append(f"owner_verdict={identity.owner_verdict!r} is not one "
                        f"of {CONFIDENCE}")

    seen: set[str] = set()
    for index, channel in enumerate(identity.channels):
        where = f"channel[{index}]"
        if channel.platform not in PLATFORMS:
            problems.append(f"{where} platform={channel.platform!r} is not one "
                            f"of {PLATFORMS}")
        if channel.confidence not in CONFIDENCE:
            problems.append(f"{where} confidence={channel.confidence!r} is not "
                            f"one of {CONFIDENCE}")
        if channel.source not in SOURCES:
            problems.append(f"{where} source={channel.source!r} is not one of "
                            f"{SOURCES}")
        if not channel.url.strip():
            problems.append(f"{where} has no url — a channel names the page it is")
        elif channel.url in seen:
            problems.append(f"{where} repeats {channel.url} — one entry per "
                            f"channel, or a reader counts a lead twice")
        seen.add(channel.url)
        if channel.confidence in ("confirmed", "absent") and not channel.evidence.strip():
            problems.append(f"{where} is {channel.confidence} with no evidence "
                            f"— a verdict that names nothing was reasoned, "
                            f"not checked")

    if identity.observations:
        from outbound import observe

        problems.extend(observe.validate_all(observe.load(identity.observations)))
    return problems


def validate_all(identities: list[Identity]) -> list[str]:
    """Every identity's problems, each prefixed with which one it was."""
    problems = []
    for index, identity in enumerate(identities):
        for problem in validate(identity):
            problems.append(f"identity[{index}] {problem}")
    return problems


def load(data) -> list[Identity]:
    """One identity or a list of them, as `observe` accepts one or many."""
    rows = data if isinstance(data, list) else [data]
    if isinstance(data, dict) and "identities" in data:
        rows = data["identities"]
    return [Identity.from_dict(row) for row in rows if isinstance(row, dict)]


def schema_help() -> str:
    """The field list, generated from the dataclasses rather than written down."""
    from dataclasses import fields as dataclass_fields

    rows = [f"    {f.name:20} {getattr(f.type, '__name__', str(f.type))}"
            for f in dataclass_fields(Identity)]
    channel_rows = [f"      {f.name:18} {getattr(f.type, '__name__', str(f.type))}"
                    for f in dataclass_fields(Channel)]
    return ("  identities, one per lead:\n" + "\n".join(rows)
            + "\n    each channel:\n" + "\n".join(channel_rows)
            + f"\n  platform is one of {PLATFORMS}\n"
              f"  confidence is one of {CONFIDENCE}\n"
              f"  source is one of {SOURCES}\n"
              "  evidence is required on confirmed and absent — a verdict that "
              "names nothing\n  was reasoned, not checked.\n"
              "  'unknown' means no tell was available. It never means the tell "
              "said no.")


def report(identities: list[Identity]) -> str:
    """The quotable summary, in the shape `observe.report` already uses."""
    problems = validate_all(identities)
    head = "VALID" if not problems else f"INVALID ({len(problems)})"
    channels = [c for i in identities for c in i.channels]
    confirmed = sum(1 for i in identities if i.has_confirmed_channel)
    absent = sum(1 for c in channels if c.confidence == "absent")
    nothing = [i for i in identities if not i.channels]

    lines = [
        f"RESOLVE: {head}, {len(identities)} identity(s), "
        f"{len(channels)} channel(s)",
        f"  {confirmed}/{len(identities)} lead(s) have at least one confirmed "
        f"channel, {absent} channel(s) name somebody else, "
        f"{len(nothing)} lead(s) have no channel at all",
    ]
    for identity in nothing:
        lines.append(f"  NO CHANNEL  {identity.name or '(no name)'} — "
                     f"free retrieval found nothing to read")
    for problem in problems:
        lines.append(f"  SCHEMA  {problem}")
    if problems:
        lines.append(schema_help())
    lines.append("  Advisory. Nothing here drops a lead — a low-confidence "
                 "channel is something not to spend on, never a reason to skip "
                 "somebody.")
    return "\n".join(lines)
