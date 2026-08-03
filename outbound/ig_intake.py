"""An Instagram profile dump -> Leads AND the observations it already carries.

`intake` maps a CSV. An Apify `instagram-profile-scraper` dump is not one, and
the last probe found that out the expensive way: 0 rows mapped on the sheet's
own headers, and the run continued by hand-remapping columns (f8a2e97).

The larger point is the second output. A profile record carries up to twelve of
the account's most recent posts, each with a **verbatim caption, a real
timestamp and its own URL** — which is exactly what `plan`'s `ig_posts` rung
pays Apify to fetch. The corpus is already in hand, so a dump like this is not
input to the machine's retrieval stage, it **is** a retrieval, made outside this
repo and priced somewhere else.

Reading it as `observe.Observation` records is what makes that true rather than
merely sayable:

- the activity floor settles from a real `published_at` instead of `unclear`,
  which is F3 — `latest_activity_date` found zero usable dates across nine
  sites and ~220,000 characters, and the floor did nothing;
- `select` ranks a real corpus, so `hook-worker` quotes something retrieved
  rather than composed;
- nothing has to fetch Instagram again to write the hook.

`retrieved_by` is `apify:ig_profile` — the actor that really produced this file,
and a key `observe` already knows. `cost_usd` is 0.0 because this repo did not
pay it; the ledger's rule is that it records what a retrieval cost *here*, and
inventing a number for somebody else's run would be a fabricated measurement.

**Two things this module does not do.** It does not infer a location: a bio is
not a location field, `qualify.check_uae` is explicit that a subject-owned field
settles the floor either way, and a "Dubai" in a caption is not one. And it does
not decide anything about the ICP — that is `outbound/triage.py`, one stage
later, on the records this one writes.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime

from outbound import observe
from outbound.normalize import Lead, classify_site, map_row

# The actor that produced a profile dump, as `observe` spells a paid rung.
RETRIEVED_BY = "apify:ig_profile"

# Instagram's display-name convention: a name, then a positioning line, with
# whatever glyph the account felt like between them. Split before the symbol
# strip below, or the separator is deleted and the two halves become one name.
_SEPARATORS = re.compile(r"\s*[|•·‣▪●⋆✦✧/]+\s*|\s+[-–—~]+\s+")

# Scraped categories come back as the literal string "None" as often as null.
_ABSENT = ("", "none", "null", "n/a")


def _clean(text: str) -> str:
    """Display text -> something a name matcher, the wall and a SERP can read.

    Instagram names are written in mathematical-bold and script code points —
    `𝐃𝐚𝐧𝐧𝐲 𝐉𝐨𝐧𝐞𝐬` is not the string "Danny Jones" and matches it nowhere. NFKC
    folds those back to ASCII letters, which is the difference between a lead
    the wall can check and a lead it silently cannot.

    Emoji and flags go too, and they go AFTER the fold: they are decoration in
    a name and noise in a search query. A stripped flag is not lost evidence —
    the biography it came from is kept verbatim in its own observation.
    """
    folded = unicodedata.normalize("NFKC", text or "")
    kept = []
    for char in folded:
        category = unicodedata.category(char)
        if category[0] in ("L", "N") or char.isspace() or char in ".,'&()":
            kept.append(char)
        elif category[0] in ("S", "C"):
            kept.append(" ")            # a glyph is a word break, not a joiner
        else:
            kept.append(" ")
    out = re.sub(r"\s+", " ", "".join(kept)).strip(" _-")
    # "S E L I N E" is one word wearing spaces. Collapse a run of three or more
    # single letters; two could be real initials.
    return re.sub(r"\b(?:\w ){2,}\w\b",
                  lambda m: m.group(0).replace(" ", ""), out)


def split_display_name(full_name: str, *, username: str = "") -> tuple[str, str]:
    """`"Rita Baki | Neuro Coach"` -> `("Rita Baki", "Neuro Coach")`.

    The suffix is the headline, and it is worth keeping: it is the lead's own
    words about what they do, which is what `qualify.check_coach` reads and what
    `email-find` puts in its query.

    A name that survives none of this falls back to the handle rather than to
    an empty string — a row with no name is a row `dedupe` cannot check against
    the wall, and that is the one check here that destroys something.
    """
    parts = [p for p in (_clean(p) for p in _SEPARATORS.split(full_name or ""))
             if p]
    name = parts[0] if parts else ""
    headline = ", ".join(parts[1:])
    if not name:
        name = _clean((username or "").replace(".", " ").replace("_", " "))
    return name, headline


def _post_records(record: dict) -> list[dict]:
    return list(record.get("latestPosts") or []) + \
        list(record.get("latestIgtvVideos") or [])


def to_lead(record: dict, *, source: str = "") -> Lead:
    """One profile record -> a Lead, with every bio link routed.

    Built through `map_row` rather than beside it, so the name split, the slug,
    the junk classification and the free handle-mismatch note are the same code
    a CSV gets — one presentation of one rule, which is what
    `_profile_name_notes` says about itself.

    **The bio link is an array.** `externalUrl` is the first of `externalUrls`,
    and 8325744 is the commit that got burned reading one of it. Every entry
    goes through `classify_site`: the first real domain becomes the site, and
    the rest land in the social fields or in `other_urls` rather than nowhere.
    """
    name, headline = split_display_name(record.get("fullName") or "",
                                        username=record.get("username") or "")
    category = (record.get("businessCategoryName") or "").strip()
    if category.lower() in _ABSENT:
        category = ""

    links = [entry.get("url") for entry in (record.get("externalUrls") or [])
             if isinstance(entry, dict) and entry.get("url")]
    if record.get("externalUrl") and record["externalUrl"] not in links:
        links.insert(0, record["externalUrl"])

    lead = map_row({
        "name": name,
        "headline": headline or category,
        "instagram": record.get("url") or "",
        "website": links[0] if links else "",
    }, source=source)

    for extra in links[1:]:
        verdict = classify_site(extra)
        if verdict.verdict == "own_site" and not lead.site_url:
            lead.site_url, lead.site_verdict = verdict.url, verdict.verdict
        elif verdict.verdict in ("own_site", "platform"):
            target = {"linkedin": "linkedin_url", "facebook": "facebook_url",
                      "youtube": "youtube_url"}.get(verdict.platform or "")
            if target and not getattr(lead, target):
                setattr(lead, target, verdict.url)
            elif verdict.url not in lead.other_urls:
                lead.other_urls.append(verdict.url)

    if headline and category and category not in lead.headline:
        lead.headline = f"{lead.headline}, {category}"
    if record.get("private"):
        lead.notes.append("private account — the dump carries no posts for it")
    return lead


def to_observations(record: dict, *, lead_key: str = "",
                    fetched_at: str = "") -> list[observe.Observation]:
    """The posts and the biography this dump already holds, kept verbatim.

    `author` is `self` only when the post's `ownerUsername` is this profile.
    Ban #7 — no third-party coverage — has been a sentence an agent is asked to
    remember; on a dump it is a field comparison, so it is made here and a
    mismatch is dropped rather than labelled.

    A caption is copied character for character. `observe`'s docstring is right
    that no check can prove that, which is exactly why nothing in this function
    trims, joins or tidies one: a summarised observation ranks fine and produces
    a hook whose quote is not on the page.

    `lead_key` is `fetch.lead_key`'s, passed in rather than derived here. It is
    the one definition — the ledger, `resolve` and `select` all join on it — and
    a second spelling of "which lead is this" is the drift `docs/spec/06-state.md`
    exists to prevent. The handle would have been the obvious local answer and
    would have joined to nothing.
    """
    username = (record.get("username") or "").strip().lower()
    stamp = fetched_at or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[observe.Observation] = []

    biography = (record.get("biography") or "").strip()
    if biography:
        out.append(observe.Observation(
            lead_key=lead_key, platform="instagram",
            url=record.get("url") or "", fetched_at=stamp,
            author="self", kind="bio", text=biography,
            cost_usd=0.0, retrieved_by=RETRIEVED_BY))

    for post in _post_records(record):
        caption = (post.get("caption") or "").strip()
        if not caption:
            continue                    # an image with no words is not a quote
        owner = (post.get("ownerUsername") or "").strip().lower()
        if owner and username and owner != username:
            continue                    # somebody else's post, on their grid
        published = (post.get("timestamp") or "")[:10]
        out.append(observe.Observation(
            lead_key=lead_key, platform="instagram",
            url=post.get("url") or "", fetched_at=stamp,
            published_at=published, author="self", kind="post",
            text=post.get("caption"), cost_usd=0.0,
            retrieved_by=RETRIEVED_BY))
    return out


def load_dump(path: str) -> list[dict]:
    """The Apify dataset as it comes off the platform: a JSON array."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("an Apify dataset is a JSON array of profile records")
    return [r for r in data if isinstance(r, dict)]


def ingest(path: str, *, source: str = "", fetched_at: str = ""
           ) -> tuple[list[Lead], list[observe.Observation]]:
    """The whole file: a Lead per profile, and every observation it carries.

    Nothing is dropped for having no posts. A private or quiet account is a
    lead with no corpus, which is a thing `triage` reads and this stage does
    not judge.
    """
    from outbound.fetch import lead_key as key_of

    leads: list[Lead] = []
    observations: list[observe.Observation] = []
    for record in load_dump(path):
        lead = to_lead(record, source=source or path)
        leads.append(lead)
        observations.extend(to_observations(
            record, lead_key=key_of(lead), fetched_at=fetched_at))
    for obs in observations:
        # Written out rather than left blank. `from_dict` generates one on load,
        # so a blank id round-trips fine in Python and joins to nothing on disk
        # — and the file is the thing a worker, a diff and `hook --against` read.
        if not obs.obs_id:
            obs.obs_id = observe.make_id(obs)
    return leads, observations


def profile(leads: list[Lead], observations: list[observe.Observation]) -> dict:
    """The shape of the dump, in `normalize.profile`'s voice.

    `with_observations` is the number that matters and it has no equivalent in
    a CSV intake: it is how many leads arrived with the hook stage's raw
    material already paid for.
    """
    from outbound.fetch import lead_key as key_of

    by_lead: dict[str, int] = {}
    posts = 0
    for obs in observations:
        if obs.kind != "post":
            continue                    # a bio is not evidence anyone posted
        by_lead[obs.lead_key] = by_lead.get(obs.lead_key, 0) + 1
        posts += 1
    return {
        "total": len(leads),
        "with_site": sum(1 for lead in leads if lead.site_url),
        "social_only": sum(1 for lead in leads
                           if not lead.site_url and lead.social_urls()),
        "no_research_target": sum(1 for lead in leads
                                  if not lead.has_research_target()),
        "with_observations": len(by_lead),
        "observations": len(observations),
        "posts": posts,
        "no_posts": sum(1 for lead in leads if not by_lead.get(key_of(lead))),
    }
