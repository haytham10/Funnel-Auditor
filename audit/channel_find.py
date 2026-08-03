"""A lead's own channels, found in search results — fetch-agnostic.

`email_find` learns an address somebody else published. This learns a **channel**
somebody else indexed: the LinkedIn profile, the Instagram account, the personal
site. It exists because a directory list arrives with contact details and no
channels at all, and a channel is what the machine actually spends on — q1-q3's
hooks came off `li_posts` and `li_profile`, and a lead with no LinkedIn URL has
no hook rung to buy.

The name is `channel` and not `profile` because `resolve` already owns that
noun: it is the stage that decides "which channels are plausibly this lead's
own, and on what evidence". This module produces candidates in that vocabulary
and `to_channels` hands them over in that shape.

**It never fetches.** It takes search results somebody else retrieved and owns
query building, merge, the noise filter, corroboration, provenance and ranking —
exactly like `email_find` and `footprint`, and for the reason `footprint`'s
docstring records: when the fetch layer under a module like this was retired,
being fetch-agnostic made it a deletion rather than a rewrite.
`audit/apify.py:google_search` is today's layer.

## The rule this module is built around

**A URL needs a reason to be believed this lead's**, and the stakes are higher
here than for an address.

`email_find` shipped without that rule and reported FOUND four times in five on
strangers' addresses. A wrong URL is worse in a way that matters: an address at
least has a local part that can carry a name, and a wrong one usually bounces —
`email-verify` caught the one fabrication that got through. A wrong LinkedIn URL
does none of that. It **verifies clean, scrapes clean, and produces a real,
quotable, re-fetchable hook about a real person who is not the lead.** Every
downstream gate checks the content and none of them checks *whose*. `hook`
confirms the quote is on the page. `hook-verifier` re-fetches and confirms it is
still there. `lint` confirms no number was invented. All four pass, and the
email goes to a coach describing a stranger's post.

So corroboration is the whole of this module, and an uncorroborated URL is a
**blank field, never a best guess**.

## Why the drops are kept

`unrelated` carries every rejected URL with the reason it was rejected. The
filter is a heuristic; the count is how anybody notices it going wrong. A zero
across twenty leads means the filter is not running, not that the list is clean
— that is `email_find`'s argument and it applies unchanged.

## Two things this module deliberately does not do

**No AI Overview.** `docs/spec/05-pipeline.md` already says do not pay for it
five hundred times, and there is nothing here worth buying it for: `email_find`
uses it for an absence verdict, and "this coach has no LinkedIn" is a fact the
organic results state perfectly well by not containing one.

**No observations.** A SERP snippet is Google's excerpt, not verbatim page text,
and `observe`'s contract is that `text` is what the page says. Minting an
observation from a snippet would put an unverifiable quote into the corpus
`select` ranks and `hook-worker` quotes from — the exact fabrication class
`hook-verifier` exists to catch, arriving through the one door it does not
watch. This module returns channels. The hook stage still fetches.
"""

from __future__ import annotations

import re
from typing import Any

from audit.email_check import name_tokens
from audit.urls import PLATFORM_BRANDS, registrable_domain
from outbound.resolve import handle_of, score_channel

# What this module looks for. `site` is not a platform in `resolve`'s sense —
# it is the absence of one — but it is the third thing missing from a directory
# row and it is found in the same result set.
PLATFORMS_SOUGHT = ("linkedin", "instagram", "site")

# How strong the reason was. Recorded per candidate because the two tiers have
# genuinely different error rates and a later reader should be able to tell a
# handle match from a circumstantial one.
#
#   handle        the URL itself carries their name. Nearly unfalsifiable.
#   corroborated  the URL half-carries it and the result page vouches for it.
TIERS = ("handle", "corroborated")

# Hosts that are a directory, an aggregator or a marketplace. A coach's ICF
# listing, their Yellow Pages entry and their profile on a coach-matching site
# all name them in full and are none of them their own channel. Without this,
# `apps.coachingfederation.org` would be accepted as the personal site of every
# lead on an ICF-sourced list — the source that produced the list becoming the
# thing it enriches.
DIRECTORY_HOSTS = {
    "coachingfederation.org", "credentialedcoachfinder.com", "yellowpages.ae",
    "yelp.com", "noon.com", "connect.ae", "dubizzle.com", "bayut.com",
    "glassdoor.com", "indeed.com", "crunchbase.com", "zoominfo.com",
    "rocketreach.co", "signalhire.com", "apollo.io", "lusha.com",
    "trustpilot.com", "clutch.co", "goodfirms.co", "wikipedia.org",
    "bark.com", "thumbtack.com", "coach.me", "noomii.com", "lifecoachhub.com",
    "coachfederation.org", "medium.com", "eventbrite.com", "meetup.com",
    "amazon.com", "books.google.com", "researchgate.net", "academia.edu",
    # The people-search aggregators, added 2026-08-03. Each publishes a page per
    # person, titled with their name, and a live SERP over 300 coaches returned
    # them constantly. `idcrawl.com/christine-harb` is not Christine Harb's
    # website however exactly it carries her name — it is a scraper's index of
    # her, and the same is true of every host on this line.
    "idcrawl.com", "contactout.com", "bayt.com", "naukrigulf.com",
    "scribd.com", "studylib.net", "slideshare.net", "issuu.com",
    "pagesjaunes.ae", "connectingdots.ae", "peekyou.com", "spokeo.com",
    "whitepages.com", "truepeoplesearch.com", "aeroleads.com", "leadiq.com",
    "salesql.com", "getprospect.com", "snov.io", "hunter.io",
}

# Instagram path segments that are the app rather than an account. `resolve`'s
# `_OPAQUE_SEGMENTS` folds these to "" so they can never be read as a handle;
# this set is the routing half — a `/p/` URL is a post, not a profile, and even
# a post by the right person is not the channel we are looking for.
_IG_RESERVED = {"p", "reel", "reels", "tv", "stories", "explore", "accounts",
                "direct", "about", "legal", "developer", "privacy", "challenge"}

_LINKEDIN_PERSON = re.compile(r"^/in/[^/]+", re.I)

# Words in a result's title or snippet that place the lead. A SERP about the
# right Mohammed Ali in Dubai says Dubai; one about a different Mohammed Ali
# usually does not.
#
# **The Arabic half is not optional.** `google_search` runs with
# `countryCode=ae` on purpose, and Google answers a UAE-geo'd query about a UAE
# person by rendering the location in Arabic. Six of the nine accepted profiles
# that stated a location at all stated it as `دبي` or `الإمارات العربية المتحدة`,
# and an ASCII-only list read every one of them as "does not say UAE" — which
# would have made the location rule below drop six correct leads to catch two
# wrong ones.
_UAE_WORDS = ("uae", "u.a.e", "emirates", "dubai", "abu dhabi", "sharjah",
              "ajman", "fujairah", "ras al khaimah", "umm al quwain",
              "الإمارات", "الامارات", "دبي", "أبو ظبي", "ابو ظبي", "الشارقة",
              "عجمان", "الفجيرة", "رأس الخيمة", "ام القيوين")

# LinkedIn prints a profile's location in a predictable slot, in whichever
# language Google rendered the result in.
_LOCATION_RE = re.compile(r"(?:location|الموقع)\s*[:：]?\s*([^·|•\n]{2,60})", re.I)

# Words that place them in this trade. Weaker than the above on this list,
# because every lead here is a coach and so is every competing result.
_COACH_WORDS = ("coach", "coaching", "icf", " mcc", " pcc", " acc",
                "mentor", "facilitator")


class ChannelFindError(RuntimeError):
    """A malformed search record — never a fetch failure, since this module
    never fetches anything itself."""


def build_queries(name: str, *, headline: str = "", city: str = "",
                  domains: tuple = (), shape: str = "one") -> list[str]:
    """The query or queries for one lead.

    `shape="one"` is a single plain search for the person. A coach's own
    LinkedIn, Instagram and website are usually the highest-authority pages for
    their own name, so one SERP can carry all three, and at $0.0025 a page the
    difference over 300 leads is real.

    `shape="two"` adds a site-scoped LinkedIn query. It buys precision on the
    one channel where precision matters most and where a plain search is most
    likely to be crowded out — a common name returns ten LinkedIn profiles and
    Google picks by authority, not by which one is in Dubai.

    **The city is in the query and the credential is not.** `email_find` learned
    that a bare name collides and that the discriminating term has to be one the
    *right* page carries; a coach's LinkedIn headline says Dubai far more often
    than it says PCC, and putting `MCC` in a query mostly finds the ICF
    directory we already scraped.

    A known domain goes in for the same reason `email_find.build_query` puts one
    there — a person is indexed beside their business name — but never a
    platform host, because searching `linkedin.com` searches for LinkedIn.
    """
    clean_name = _query_name(name)
    if not clean_name:
        return []

    parts = [f'"{clean_name}"']
    if city:
        parts.append(city.strip())
    parts.append("coach")
    for domain in domains:
        registrable = registrable_domain(domain)
        if registrable and registrable not in PLATFORM_BRANDS:
            parts.append(registrable)
            break

    plain = " ".join(p for p in parts if p)
    if shape == "one":
        return [plain]
    scoped = f'site:linkedin.com/in "{clean_name}"' + (f" {city.strip()}" if city else "")
    return [plain, scoped]


def _query_name(name: str) -> str:
    """The name as a searcher would type it.

    A directory prints the name on the certificate. One real row reads
    `Catharina (Cindy) Leonarda Maria Van De Kreke-Freens`, and searching seven
    tokens in quotes finds nothing at all — the person is indexed everywhere
    else as Cindy van de Kreke. So a parenthetical is treated as what it is, a
    preferred name, and replaces the given name rather than sitting inside the
    quotes as literal text.
    """
    raw = (name or "").strip()
    nickname = re.search(r"\(([^)]+)\)", raw)
    if nickname:
        preferred = nickname.group(1).strip()
        rest = re.sub(r"\([^)]*\)", " ", raw).split()
        # The preferred name replaces the first given name; the family name is
        # whatever the certificate ends with.
        if preferred and len(rest) >= 2:
            raw = " ".join([preferred] + rest[1:])
        elif preferred:
            raw = preferred
    return re.sub(r"\s+", " ", raw).strip()


def _organic_rows(item: dict) -> list[dict]:
    rows = item.get("organicResults") or item.get("organic_results") or []
    return [r for r in rows if isinstance(r, dict)]


def _platform_of(url: str) -> str:
    """Which of the three things this URL is, or "" for something we do not
    want. Structural only — nothing here looks at the name yet."""
    host = registrable_domain(url)
    if not host:
        return ""
    if host == "linkedin.com":
        return "linkedin" if _LINKEDIN_PERSON.match(_path_of(url)) else ""
    if host == "instagram.com":
        segments = [s for s in _path_of(url).split("/") if s]
        if not segments or segments[0].lower() in _IG_RESERVED:
            return ""
        return "instagram"
    if host in PLATFORM_BRANDS or host in DIRECTORY_HOSTS:
        return ""
    return "site"


def _path_of(url: str) -> str:
    from urllib.parse import urlparse

    try:
        return urlparse(url if "//" in url else "//" + url).path or "/"
    except ValueError:
        return "/"


def _canonical(url: str, platform: str) -> str:
    """One URL per channel, so `linkedin.com/in/x/` and `de.linkedin.com/in/x`
    are not two candidates. Keeps the path for a profile and drops it for a
    site, where the result is usually a deep page and the channel is the host.

    **LinkedIn is truncated to `/in/<slug>`**, which the pilot needed: a SERP
    returns `linkedin.com/in/ramisukkar` and `linkedin.com/in/ramisukkar/fr`,
    the same profile under a locale suffix, and without this they arrive as two
    competing candidates and make one real profile look like an ambiguity.
    """
    host = registrable_domain(url)
    path = _path_of(url).rstrip("/")
    if platform == "site":
        return f"https://{host}"
    if platform == "linkedin":
        segments = [s for s in path.split("/") if s]
        if len(segments) >= 2:
            path = f"/in/{segments[1]}"
    return f"https://{host}{path}"


def _slug_of(url: str, platform: str) -> str:
    """The raw path segment, unfolded — digits intact."""
    segments = [s for s in _path_of(url).split("/") if s]
    if platform == "linkedin":
        return segments[1] if len(segments) >= 2 else ""
    return segments[0] if segments else ""


def _stem(value: str) -> str:
    return re.sub(r"[^a-z]+", "", (value or "").lower())


def _candidate(url: str, platform: str, row: dict, *, tokens: list[str],
               lead_domains: set[str], city: str = "") -> dict:
    """One channel with every signal a decision could need, and no decision
    made. `email_find._candidate`'s shape, one noun over."""
    title = str(row.get("title") or "")
    snippet = str(row.get("description") or row.get("snippet") or "")
    blob = f"{title} {snippet}".lower()
    blob_words = set(re.sub(r"[^a-z]+", " ", blob).split())

    # **A site has no handle, and computing one from its path is how a
    # people-search page becomes a coach's website.** `idcrawl.com/christine-harb`
    # folded to `christineharb`, matched her name exactly, and was accepted at
    # the strongest tier — as were `contactout.com/usha-kaul-saraf` and a team
    # bio at `leagrowingpeople.com/richa-singh`. A path segment on somebody
    # else's domain says who the PAGE is about, never whose channel it is; a
    # website is identified by its domain and by nothing else.
    handle = handle_of(url, platform) if platform != "site" else ""
    domain = registrable_domain(url)
    folded_name = "".join(tokens)

    return {
        "url": _canonical(url, platform),
        "platform": platform,
        "handle": handle,
        "source_url": row.get("url") or "",
        "source_title": title,
        "provenance": "organic",
        # Every token in the handle. `cindyvandekreke` carries both halves.
        "handle_full_match": bool(handle) and bool(tokens)
        and all(t in handle for t in tokens),
        "handle_partial_match": bool(handle) and any(t in handle for t in tokens),
        # ALL name tokens, never one. `email_find` learned this when "Spencer"
        # alone matched a page about a different Spencer.
        "result_names_lead": bool(tokens) and all(t in blob_words for t in tokens),
        "result_names_place": any(w in blob for w in _UAE_WORDS)
        or bool(city and city.lower() in blob),
        "result_names_coach": any(w in blob for w in _COACH_WORDS),
        "on_lead_domain": bool(domain) and domain in lead_domains,
        # `lanawl.com` for Lana WL. The site equivalent of a handle match.
        "domain_is_the_name": platform == "site" and bool(folded_name)
        and _stem(domain.rsplit(".", 1)[0]) == folded_name,
        "domain_carries_the_name": platform == "site" and bool(tokens)
        and all(t in _stem(domain) for t in tokens),
        # A slug with no digits is the vanity URL the person chose; a slug
        # ending in a hex blob is the one LinkedIn generated because the vanity
        # one was taken. Both belong to real people, which is the point — when
        # two profiles carry the same name, the one that OWNS the plain slug is
        # the stronger claim to it. It is the only honest tiebreak available,
        # and where it does not separate them nothing does.
        "vanity_slug": not re.search(r"\d", _slug_of(url, platform)),
        # The page states where this person is, and it is not here. Every lead
        # on a UAE directory is in the UAE, so a profile that prints a location
        # and prints somewhere else is a different person of the same name —
        # which is how a Dance Professor Emerita in Athens, Ohio was accepted
        # as a Dubai coach on an exact handle match.
        #
        # It only ever fires on a stated location, never on a missing one:
        # `resolve`'s rule 4 exactly — a tell was available and it said no.
        "placed_elsewhere": _placed_elsewhere(blob),
    }


def _placed_elsewhere(blob: str) -> bool:
    match = _LOCATION_RE.search(blob)
    if not match:
        return False
    lowered = blob.lower()
    return not any(word in match.group(1).lower() or word in lowered
                   for word in _UAE_WORDS)


def _judge(cand: dict) -> tuple[str, str]:
    """`(tier, why)` — accepted at a tier, or `("", why it was dropped)`.

    In order, strongest first:

      1  the handle carries every part of their name
      2  the domain IS their name (site only)
      3  it is on a domain already known to be theirs
      4  the handle carries part of the name AND the result names them in full
         AND places them or names the trade

    Rule 4 is `email_find._is_corroborated`'s third way transposed, including
    the fix that cost it four false positives: "the page names them in full"
    **alone** is not a reason, because a page being about somebody corroborates
    the page and not everything printed on it. It needs a second, independent
    property of the thing being attributed — here, the handle carrying part of
    the name.

    There is deliberately **no rule that accepts on circumstance alone.** A
    result that names the lead, says Dubai and says coach, on a URL whose handle
    carries nothing of their name, is exactly the shape of a stranger's profile
    on a page that happens to mention the lead. For a common name — and 228 of
    the 311 names on the list this was built for are two tokens — that shape is
    the majority of what a SERP returns.
    """
    # Checked before every acceptance rule, because it beats all of them: a
    # handle can carry the name perfectly and still belong to the wrong person,
    # and where the page says so it says so louder than the slug does.
    if cand["placed_elsewhere"]:
        return "", ("the profile states a location and it is not the UAE — "
                    "a different person of the same name")

    if cand["handle_full_match"]:
        return "handle", f"handle {cand['handle']!r} carries their whole name"
    if cand["domain_is_the_name"] or cand["domain_carries_the_name"]:
        return "handle", f"the domain is their name ({cand['url']})"
    if cand["on_lead_domain"]:
        return "handle", "on a domain already known to be theirs"
    if (cand["handle_partial_match"] and cand["result_names_lead"]
            and (cand["result_names_place"] or cand["result_names_coach"])):
        where = "places them in the UAE" if cand["result_names_place"] \
            else "names the trade"
        return "corroborated", (f"handle {cand['handle']!r} carries part of "
                                f"their name and the result names them in full "
                                f"and {where}")

    if not cand["handle"] and cand["platform"] != "site":
        return "", "the URL carries no name to check"
    if cand["result_names_lead"]:
        return "", ("the result names them but the URL carries no part of "
                    "their name — a page about somebody is not their channel")
    return "", (f"handle {cand['handle']!r} carries no part of their name"
                if cand["handle"] else "nothing connects this URL to them")


def _rank(cand: dict) -> tuple:
    """Most-likely-theirs first."""
    return (
        {"handle": 0, "corroborated": 1}.get(cand.get("tier"), 2),
        0 if cand["on_lead_domain"] else 1,
        0 if cand["vanity_slug"] else 1,
        0 if cand["result_names_place"] else 1,
        cand["url"],
    )


def _pick(candidates: list) -> tuple[str, str]:
    """The one URL for a platform, or `("", why not)`.

    **An ambiguous match attaches nothing.** `corpus attach` already holds this
    rule for the same reason — putting one coach's posts on another produces a
    hook that is verified, quotable and about a stranger — and the pilot proved
    this stage needs it. Six of fourteen leads came back with two or three
    LinkedIn profiles all carrying the name, and the command silently kept the
    first. For `Gitanjali Sharma` that was a one-in-three guess between three
    different real people, shipped as a confirmed channel.

    The tiebreak is the vanity slug and it is the only honest one available:
    `linkedin.com/in/melbaxter` is a slug its owner claimed, and
    `linkedin.com/in/mel-baxter-a2273277` is one LinkedIn generated because the
    plain one was taken. Where exactly one candidate holds the plain slug, that
    is a reason. Where none does — three Gitanjali Sharmas with three generated
    slugs — there is no reason, and the honest output is a blank field naming
    the competitors rather than a coin flip.
    """
    if not candidates:
        return "", ""
    ordered = sorted(candidates, key=_rank)
    best = _rank(ordered[0])[:3]
    tied = [c for c in ordered if _rank(c)[:3] == best]
    if len(tied) == 1:
        return ordered[0]["url"], ""
    return "", (f"{len(tied)} equally-good candidates and nothing separates "
                f"them ({', '.join(c['url'] for c in tied[:3])}) — a coin flip "
                f"between real people is not a find")


def find_channels(name: str, items, *, lead_domains: tuple = (),
                  city: str = "", known: dict | None = None) -> dict:
    """One lead's SERP record(s) -> corroborated, ranked channel candidates.

    Takes a LIST of records because the two-query shape produces two for one
    lead and the merge has to happen before the ranking — the same reason
    `footprint.classify_footprint_hits` takes two hit lists. A single record is
    accepted too.

    `known` is what the row already carried (`linkedin_url`, `instagram_url`,
    `site_url`). A channel already in hand is not re-derived and not overwritten:
    the row is a stronger provenance than a search result, and nine leads on the
    list this was built for arrived with a LinkedIn in their website column.
    """
    if isinstance(items, dict):
        items = [items]
    items = [i for i in (items or []) if isinstance(i, dict)]

    tokens = name_tokens(name, min_len=3)
    domains = {registrable_domain(d) for d in lead_domains if d}
    domains.discard("")
    known = {k: v for k, v in (known or {}).items() if v}

    seen: set[str] = set()
    accepted: list[dict] = []
    unrelated: list[dict] = []
    organic = 0

    for item in items:
        for row in _organic_rows(item):
            url = str(row.get("url") or "").strip()
            if not url:
                continue
            organic += 1
            platform = _platform_of(url)
            if not platform:
                continue
            cand = _candidate(url, platform, row, tokens=tokens,
                              lead_domains=domains, city=city)
            if cand["url"] in seen:
                continue
            seen.add(cand["url"])
            tier, why = _judge(cand)
            cand["why"] = why
            if tier:
                cand["tier"] = tier
                accepted.append(cand)
            else:
                unrelated.append(cand)

    accepted.sort(key=_rank)
    picked = {"linkedin_url": "", "instagram_url": "", "site_url": ""}
    field_of = {"linkedin": "linkedin_url", "instagram": "instagram_url",
                "site": "site_url"}
    ambiguous = {}
    for platform, field in field_of.items():
        url, why = _pick([c for c in accepted if c["platform"] == platform])
        picked[field] = url
        if why:
            ambiguous[platform] = why

    # The row wins. It is a stronger provenance than anything bought here, and
    # it settles an ambiguity the search could not: a lead who arrived with a
    # LinkedIn URL is not a coin flip whatever the SERP returned.
    from_row = set()
    for field, value in known.items():
        if field in picked and value:
            picked[field] = value
            from_row.add(field)
            ambiguous.pop(field.replace("_url", ""), None)

    # The verdict describes the lead's channel state, and `from_row` records
    # which of it was free. An earlier cut excluded row-supplied fields here, so
    # a lead whose row already carried a LinkedIn that the search then
    # independently confirmed came back UNCORROBORATED while holding a verified
    # URL — a verdict and a field disagreeing about the same lead.
    if any(picked.values()):
        verdict = "FOUND"
    elif ambiguous:
        verdict = "AMBIGUOUS"
    elif organic:
        verdict = "UNCORROBORATED"
    else:
        verdict = "NONE"

    return {
        "verdict": verdict,
        "candidates": accepted,
        "unrelated": unrelated,
        "accepted": picked,
        "ambiguous": ambiguous,
        "from_row": sorted(from_row),
        "organic_results": organic,
        "reason": _reason(verdict, accepted, unrelated, organic, ambiguous),
    }


def _reason(verdict: str, accepted: list, unrelated: list, organic: int,
            ambiguous: dict | None = None) -> str:
    """Why, in the words an operator needs to decide whether to look by hand.

    **Three of the four verdicts leave a field blank and they are not the same
    finding.** `NONE` means nobody was found. `UNCORROBORATED` means somebody
    was found and dropped as probably not them. `AMBIGUOUS` means two or more
    people of that name were found and nothing separates them. The first is a
    fact about the coach, the second a fact about this filter, and the third is
    the only one a human could settle in thirty seconds — which is exactly why
    it has to be tellable apart from the other two.
    """
    dropped = len(unrelated)
    ambiguous = ambiguous or {}
    if verdict == "FOUND":
        kinds = ", ".join(sorted({c["platform"] for c in accepted}))
        line = (f"{len(accepted)} channel(s) accepted ({kinds}), {dropped} "
                f"dropped as somebody else's")
        if ambiguous:
            line += f"; {', '.join(ambiguous)} left blank as ambiguous"
        return line
    if verdict == "AMBIGUOUS":
        return "; ".join(ambiguous.values())
    if verdict == "UNCORROBORATED":
        return (f"{organic} organic result(s), {dropped} candidate URL(s), none "
                f"with a reason to be believed theirs — a blank field here means "
                f"found and rejected, not nothing found")
    return "no organic result carried a channel URL at all"


def accepted(result: dict) -> dict:
    """The three fields, for a caller that wants only the answer."""
    return dict(result.get("accepted") or
                {"linkedin_url": "", "instagram_url": "", "site_url": ""})


def to_channels(name: str, result: dict) -> list[dict]:
    """The accepted candidates as `resolve.Channel` dicts, `source="serp"`.

    Scored through `resolve.score_channel` rather than by translating this
    module's tier into a confidence, so there is one vocabulary for "is this
    theirs" and not two. The corroborating result page arrives as `from_page`
    with `page_owner="confirmed"`, which is rule 3's existing shape — provenance
    promotes and never demotes.

    **`score_channel` is allowed to disagree, and its answer is the one that
    ships.** A tier-`corroborated` candidate is accepted here on circumstance
    the handle alone does not support, and `resolve` is entitled to call that
    handle `absent`; writing `confirmed` over the top would make this module the
    authority on a question `resolve` owns, and would hide the weaker tier from
    every reader downstream. `site` is skipped because it is not a channel in
    `resolve`'s sense.
    """
    tokens = name_tokens(name, min_len=3)
    out = []
    for cand in result.get("candidates") or []:
        if cand["platform"] == "site":
            continue
        handle, confidence, evidence = score_channel(
            cand["url"], cand["platform"], tokens,
            source="serp", from_page=cand.get("source_title", ""),
            page_owner="confirmed" if cand.get("tier") == "corroborated" else "unknown")
        out.append({
            "platform": cand["platform"],
            "url": cand["url"],
            "handle": cand.get("handle") or handle,
            "confidence": confidence,
            "evidence": f"{cand.get('why') or evidence} [serp, {cand.get('tier')}]",
            "source": "serp",
        })
    return out


def report(name: str, result: dict) -> str:
    """One lead's line, quotable."""
    lines = [f"CHANNEL FIND: {result['verdict']} — {name}: {result['reason']}"]
    for cand in result.get("candidates") or []:
        lines.append(f"    {cand['platform']:9s} {cand['url']}  "
                     f"[{cand['tier']}] {cand['why']}")
    for cand in (result.get("unrelated") or [])[:4]:
        lines.append(f"    dropped   {cand['url']}  {cand['why']}")
    return "\n".join(lines)


def print_find(name: str, items, **kwargs) -> int:
    """Exit code for one lead: 0 FOUND, 1 open work."""
    result = find_channels(name, items, **kwargs)
    print(report(name, result))
    return 0 if result["verdict"] == "FOUND" else 1
