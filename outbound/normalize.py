"""Raw list row -> Lead, with the junk stripped and the platform URLs routed.

Stage 1 of the machine. Cheap, offline, and it runs before anything that costs
money, because the alternative is paying to research an auto garage sitting on
an expired coach domain.

Three jobs:

1. **Column mapping.** Lists arrive from directories, exports and scrapes with
   whatever headers that source felt like. `map_row` accepts the common
   spellings ("Full Name" / "name" / "contact", "Website" / "site" / "url")
   so a new list usually needs no config at all.

2. **Junk-domain classification.** 24 of 137 "websites" on the last real list
   were not websites. `classify_site` sorts a URL into one of four verdicts:

       own_site   a real domain that is plausibly theirs -> fetch it
       platform   instagram.com/x, linkedin.com/in/x, a linktree -> NOT junk,
                  this is a direct pointer into social research
       parked     hugedomains, godaddy for-sale, expired-and-repurposed
       junk       accounts.google.com, an image file, a bare TLD, nonsense

   The `platform` verdict is the one that matters and the one the old pipeline
   got wrong. A LinkedIn URL in the website column is not a dead end, it is the
   best research target on the row. Discarding it threw away real leads.

3. **Dead-site survival.** A lead with no live site is only parked when it also
   has no usable social handle. Social research alone can carry a whole lead,
   and on the last list 199 of 336 rows had a dead or missing site, so a hard
   site gate was throwing away most of the market.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse

from audit.urls import normalize as normalize_url, registrable_domain, slugify

# ---------------------------------------------------------------- column names

# Lowercased, punctuation-stripped header -> our field name. Ordered by how
# often each spelling actually turns up in a directory export.
COLUMN_ALIASES: dict[str, str] = {
    "name": "name", "fullname": "name", "contact": "name",
    "contactname": "name", "coach": "name", "personname": "name",
    "firstname": "first_name", "first": "first_name", "givenname": "first_name",
    "lastname": "last_name", "last": "last_name", "surname": "last_name",
    "email": "email", "emailaddress": "email", "workemail": "email",
    "website": "site_url", "site": "site_url", "url": "site_url",
    "websiteurl": "site_url", "siteurl": "site_url", "web": "site_url",
    "domain": "site_url", "homepage": "site_url",
    # Sales-tool exports name the site after the company, not the person. The
    # first real list ran with `companyWebsite` and mapped ZERO of 13 sites:
    # every lead fell through to social-only research and the whole free
    # site-read tier was skipped without a single warning.
    "companywebsite": "site_url", "companyurl": "site_url",
    "companysite": "site_url", "companydomain": "site_url",
    "businesswebsite": "site_url", "personalwebsite": "site_url",
    "weburl": "site_url", "webaddress": "site_url", "websiteaddress": "site_url",
    "domainname": "site_url", "companyweb": "site_url",
    "linkedin": "linkedin_url", "linkedinurl": "linkedin_url",
    "linkedinprofile": "linkedin_url", "li": "linkedin_url",
    "instagram": "instagram_url", "instagramurl": "instagram_url",
    "ig": "instagram_url",
    "facebook": "facebook_url", "facebookurl": "facebook_url",
    "youtube": "youtube_url", "youtubeurl": "youtube_url",
    "city": "city", "location": "city", "country": "country",
    "company": "company", "business": "company", "organisation": "company",
    "organization": "company", "companyname": "company",
    "title": "headline", "headline": "headline", "jobtitle": "headline",
    "phone": "phone", "phonenumber": "phone", "mobile": "phone",
}


def _canon_header(header: str) -> str:
    """"Website URL" / "website_url" / "websiteUrl" all collapse to one key.

    Spaces and punctuation go too, so the alias table only needs the letters.
    Keeping a spaced form and an unspaced form as separate aliases is how
    "Website URL" silently failed to map while "Website" worked.
    """
    return re.sub(r"[^a-z]+", "", (header or "").lower())


# ------------------------------------------------------------ site classifying

# Podcast hosts. Rung 2 of the hook ladder is "podcasts and YouTube" — the rung
# that exists for the coaches who do not post — and until now no podcast host
# was recognised anywhere in this repo, so that rung was served entirely by an
# agent improvising a web search.
#
# **A podcast host is never a coach's own site**, which is what makes routing
# them here safe. `linkin.bio`, `carrd.co`, `about.me` and `solo.to` are NOT in
# this map for the opposite reason: a real coach's website can be
# `sarah.carrd.co`, and classifying it as a platform would stop tier 0 reading
# it and take its text out of `sites.json`, which every research worker
# consumes. They stay in `dedupe._NON_IDENTIFYING_HOSTS`, which is the other
# half of this list and has drifted from it; the two reconcile when `observe`
# owns both paths.
#
# `podcasts.apple.com` is a full host, not a registrable domain — Apple's is
# `apple.com`, and claiming that would label every Apple URL a podcast.
# `classify_site` matches on either, which is why it can sit here.
PODCAST_HOSTS: dict[str, str] = {
    "spotify.com": "podcast",
    "podcasts.apple.com": "podcast",
    "anchor.fm": "podcast",
    "buzzsprout.com": "podcast",
    "podbean.com": "podcast",
    "libsyn.com": "podcast",
    "simplecast.com": "podcast",
    "transistor.fm": "podcast",
    "captivate.fm": "podcast",
    "redcircle.com": "podcast",
    "castbox.fm": "podcast",
    "spreaker.com": "podcast",
}

# Social and link-in-bio hosts. A URL here is a research target, never junk.
PLATFORM_HOSTS: dict[str, str] = {
    "instagram.com": "instagram",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "tiktok.com": "tiktok",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "linktr.ee": "linkinbio",
    "beacons.ai": "linkinbio",
    "bio.link": "linkinbio",
    "stan.store": "linkinbio",
    "milkshake.app": "linkinbio",
    "taplink.cc": "linkinbio",
    **PODCAST_HOSTS,
}

# Domain-for-sale parkers and registrar holding pages.
PARKED_HOSTS = (
    "hugedomains.com", "forsale.godaddy.com", "afternic.com", "sedo.com",
    "dan.com", "undeveloped.com", "domainmarket.com", "buydomains.com",
    "namecheap.com", "parkingcrew.net", "bodis.com", "sav.com",
)

# Never a lead's own site: infrastructure, SaaS logins, generic booking tools
# with no owner information on them.
JUNK_HOSTS = (
    "accounts.google.com", "outlook.live.com", "outlook.office.com",
    "mail.google.com", "docs.google.com", "drive.google.com",
    "sites.google.com", "wa.me", "api.whatsapp.com", "t.me",
    "paperbell.me", "calendly.com", "cal.com", "zoom.us",
    "eventbrite.com", "meetup.com", "gmail.com", "example.com",
    # Hosted booking and landing pages. The same family as calendly above, and
    # they were missing, so `classify_site` called `subscribepage.io` and
    # `tejomaya.setmore.com` a coach's own site on 2026-08-03. Two costs: the
    # list's own-domain rate — the number that predicts whether it can produce
    # emails at all — reads high, and `email-enrich` is invited to guess
    # `name@setmore.com`, which is a real domain belonging to a SaaS company.
    "setmore.com", "subscribepage.io", "onlinecoaching.io", "mailchi.mp",
    "trainerize.com", "everfit.io", "practicebetter.io", "acuityscheduling.com",
    "square.site", "wixsite.com", "app.link",
)

_ASSET_RE = re.compile(r"\.(png|jpe?g|gif|webp|svg|css|js|pdf|zip)(\?|$)", re.I)


@dataclass
class SiteVerdict:
    """What `classify_site` decided, and why."""
    verdict: str            # own_site | platform | parked | junk | missing
    url: str = ""           # normalized, empty when nothing usable
    platform: str = ""      # instagram | linkedin | ... when verdict=platform
    reason: str = ""

    def is_research_target(self) -> bool:
        return self.verdict in ("own_site", "platform")


def classify_site(raw: str) -> SiteVerdict:
    """Sort one 'website' cell into own_site / platform / parked / junk / missing.

    A platform URL is NOT a rejection. It routes the lead into social research
    instead of a site fetch, which is the fix for the old pipeline discarding
    24 rows whose only crime was having a LinkedIn URL in the website column.
    """
    value = (raw or "").strip()
    if not value or value.lower() in ("n/a", "na", "none", "-", "null"):
        return SiteVerdict("missing", reason="no value")

    if not re.match(r"^[a-z][a-z0-9+.-]*://", value, re.I):
        value = "https://" + value.lstrip("/")

    try:
        url = normalize_url(value)
        host = urlparse(url).netloc.lower()
    except Exception:
        return SiteVerdict("junk", reason="unparseable")

    if not host or "." not in host:
        return SiteVerdict("junk", reason="no host")

    if _ASSET_RE.search(url):
        return SiteVerdict("junk", url=url, reason="asset file, not a page")

    domain = registrable_domain(host)

    for platform_host, label in PLATFORM_HOSTS.items():
        # Host OR registrable domain. Every other key here IS a registrable
        # domain, so matching the host too is strictly additive — and it is
        # what lets `podcasts.apple.com` be a key without `apple.com` becoming
        # one, which would label every Apple URL a podcast.
        if domain == platform_host or host == platform_host:
            # A bare platform root with no profile path tells us nothing.
            path = urlparse(url).path.strip("/")
            if not path:
                return SiteVerdict("junk", url=url, reason=f"bare {label} root")
            return SiteVerdict("platform", url=url, platform=label,
                               reason=f"{label} profile, route to social research")

    # Registrable domain only, never a substring of the host. `"dan.com" in
    # host` matched jordan.com and sudan.com, and `"sav.com"` matched
    # coachsav.com — real coach domains, dropped as for-sale before any
    # research ran. Same silent-loss failure the platform routing above exists
    # to prevent, reintroduced against a different host list.
    if domain in PARKED_HOSTS:
        return SiteVerdict("parked", url=url, reason="domain for sale")

    if domain in JUNK_HOSTS or host in JUNK_HOSTS:
        return SiteVerdict("junk", url=url, reason="not an owned site")

    return SiteVerdict("own_site", url=url, reason="")


# ------------------------------------------------------------------- the Lead


@dataclass
class Lead:
    """One row, normalized. Every downstream stage reads and writes this."""

    name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    site_url: str = ""
    site_verdict: str = ""
    linkedin_url: str = ""
    instagram_url: str = ""
    facebook_url: str = ""
    youtube_url: str = ""
    city: str = ""
    country: str = ""
    company: str = ""
    headline: str = ""
    phone: str = ""
    other_urls: list[str] = field(default_factory=list)
    source: str = ""
    slug: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def domain(self) -> str:
        return registrable_domain(self.site_url) if self.site_url else ""

    def social_urls(self) -> list[str]:
        """Every public profile worth researching, including the ones with no
        dedicated field — TikTok, Twitter, and the link-in-bio hosts."""
        named = (self.linkedin_url, self.instagram_url,
                 self.facebook_url, self.youtube_url)
        return [u for u in named if u] + list(self.other_urls)

    def has_research_target(self) -> bool:
        """Enough to research at all? A live site OR any social profile."""
        return bool(self.site_url) or bool(self.social_urls())

    def to_dict(self) -> dict:
        return asdict(self)


def _split_name(lead: Lead) -> None:
    """Fill whichever of name / first_name / last_name the source left out."""
    if lead.name and not lead.first_name:
        parts = [p for p in re.split(r"\s+", lead.name.strip()) if p]
        if parts:
            lead.first_name = parts[0]
            if len(parts) > 1 and not lead.last_name:
                lead.last_name = parts[-1]
    if not lead.name:
        lead.name = " ".join(p for p in (lead.first_name, lead.last_name) if p)


def map_row(row: dict, *, source: str = "") -> Lead:
    """One raw CSV row -> a Lead, with the site cell classified and platform
    URLs routed into the social fields rather than dropped."""
    lead = Lead(source=source)
    extra_platforms: list[SiteVerdict] = []

    for header, value in row.items():
        field_name = COLUMN_ALIASES.get(_canon_header(header))
        if not field_name or not (value or "").strip():
            continue
        value = value.strip()

        if field_name == "site_url":
            verdict = classify_site(value)
            # Only record the verdict that matches what we KEPT. `site_url` is
            # only ever set (never cleared), so with two site-ish columns the
            # last one processed used to stamp its verdict over the first —
            # leaving a lead with a good site carrying verdict "junk" and a note
            # saying the site was dropped. Nothing in Python reads the field,
            # but an operator reading the profile does.
            # Record the verdict only when it describes what we KEPT.
            if verdict.verdict == "own_site" or not lead.site_url:
                lead.site_verdict = verdict.verdict
            if verdict.verdict == "own_site":
                lead.site_url = verdict.url
                lead.site_verdict = verdict.verdict
            elif verdict.verdict == "platform":
                extra_platforms.append(verdict)
                lead.notes.append(f"site column held a {verdict.platform} URL")
            elif verdict.verdict in ("parked", "junk"):
                lead.notes.append(f"site dropped: {verdict.reason}")
        elif field_name in ("linkedin_url", "instagram_url",
                            "facebook_url", "youtube_url"):
            verdict = classify_site(value)
            if verdict.verdict == "platform":
                setattr(lead, field_name, verdict.url)
        else:
            setattr(lead, field_name, value)

    # A platform URL from the website column fills its own social field, but
    # only when that field is still empty — an explicit LinkedIn column wins.
    # Platforms with no dedicated field (TikTok, Twitter, every link-in-bio
    # host) land in `other_urls` rather than being dropped: six of the ten
    # PLATFORM_HOSTS had no `target` here, so `classify_site` correctly called
    # them research targets and `map_row` then threw them away, leaving the
    # lead counted as "nothing to work". That is the 24-discarded-rows bug
    # again, one host list over.
    for verdict in extra_platforms:
        target = {
            "instagram": "instagram_url", "linkedin": "linkedin_url",
            "facebook": "facebook_url", "youtube": "youtube_url",
        }.get(verdict.platform)
        if target and not getattr(lead, target):
            setattr(lead, target, verdict.url)
        elif not target and verdict.url not in lead.other_urls:
            lead.other_urls.append(verdict.url)

    _split_name(lead)
    lead.slug = slugify(lead.name or lead.domain or "lead")
    lead.notes.extend(_profile_name_notes(lead))
    return lead


def _profile_name_notes(lead: "Lead") -> list[str]:
    """Free ownership check: does a profile URL's own handle contain the name?

    About 40 of 151 rows on the first batch pointed at somebody else — name
    collisions, a coach's training-school site, an Ohio retreat house. Every one
    was found by a worker, by hand, after the fetch had already been paid for.
    A LinkedIn `/in/<slug>` is the cheapest possible tell and costs no request
    at all.

    **A note, never a drop.** Plenty of real people have a handle that is a
    brand, a nickname, or their name with digits after it. This exists so the
    bad rows are visible before the money, not so the machine can act on them.

    The handle extraction and the match are `outbound/resolve.py`'s, not a
    second copy: this is the prose presentation of the same rule `resolve`
    returns a verdict for. Its `handle_of` also returns "" for an id that cannot
    carry a name, which the local version could not — it did
    `url.rsplit("/", 1)[-1]` and would have reported `youtube.com/channel/UC1a2b3c`
    as a name mismatch. Two presentations of one rule; not three implementations.
    """
    from audit.email_check import name_tokens
    from outbound.resolve import handle_of, handle_matches

    tokens = name_tokens(lead.name or "", min_len=3)
    if not tokens:
        return []
    notes = []
    for field_name, label, platform in (("linkedin_url", "LinkedIn", "linkedin"),
                                        ("instagram_url", "Instagram", "instagram")):
        url = getattr(lead, field_name, "")
        if not url:
            continue
        handle = handle_of(url, platform)
        if handle and not handle_matches(handle, tokens):
            notes.append(f"{label} handle does not contain this lead's name "
                         f"({url}) — confirm it is them before spending on it")
    return notes


def unmapped_headers(path: str) -> list[str]:
    """Columns the alias table does not know, so a list can say what it dropped.

    `map_row` skips any header it cannot map, which is right — exports carry
    plenty of noise. But it is silent, and silence is how a real list ran with
    `companyWebsite` and mapped zero of thirteen sites: every lead fell through
    to social-only research and the entire free site-read tier was skipped with
    nothing printed. A dropped column that turns out to matter should be one
    line of output, not an archaeology session.
    """
    with open(path, newline="", encoding="utf-8-sig") as handle:
        headers = next(csv.reader(handle), [])
    return [h for h in headers
            if h and h.strip() and not COLUMN_ALIASES.get(_canon_header(h))]


def load_csv(path: str, *, source: str = "") -> list[Lead]:
    """Read a raw list into Leads. Blank rows and header-only files are fine."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    leads = [map_row(row, source=source or path) for row in rows]
    return [lead for lead in leads if lead.name or lead.email or lead.site_url]


def profile(leads: list[Lead]) -> dict:
    """Batch shape before anything is spent. Print this, then decide.

    **`with_site` is the reachability number and nobody was reading it.** A lead
    with no branded domain has nothing for `email-enrich` to guess against, and
    on 2026-08-03 an Instagram list where 13% of the ICP owned a domain shipped
    2 emails from 237 rows. Whether a list can produce emails at all is a
    property of the list, knowable here, before a cent.
    """
    parked = [lead for lead in leads if not lead.has_research_target()]
    return {
        "total": len(leads),
        "with_site": sum(1 for lead in leads if lead.site_url),
        "social_only": sum(1 for lead in leads
                           if not lead.site_url and lead.social_urls()),
        "with_email": sum(1 for lead in leads if lead.email),
        "no_research_target": len(parked),
        "parked_names": [lead.name for lead in parked][:20],
    }
