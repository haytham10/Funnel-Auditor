"""
Published-address retrieval from search results — fetch-agnostic.

The third and last way this machine can learn an address, and the only one that
looks anywhere but the lead's own pages:

    harvest   `audit/extract.py`     an address printed on a page tier 0 read
    guess     `audit/email_enrich.py` nominative permutation on their own domain
    find      this module             an address somebody else published

It exists because 2026-08-03's probe measured all five leads of a real
Instagram list as unreachable, and a plain search found addresses for four of
them. Two of those addresses were on domains nothing else in the machine had
ever seen: `lanawl.com` appears in no bio link and no `externalUrls` entry, and
`whiteantlergroup.com` is a lead's second company. **A coach's address is
routinely published by an accreditation body, a directory, a company page or a
podcast, and never on their own site at all** — which is the only place the
other two paths look.

**This module never fetches.** It takes search results somebody else retrieved
and owns the merge, the noise filter, the provenance and the ranking, exactly
like `audit/footprint.py` and for the same reason: when the fetch layer under
that module was retired, being fetch-agnostic made it a deletion rather than a
rewrite. `audit/apify.py:google_search` is today's layer and the agent's own
WebSearch fits the same shape.

## The one rule that makes this safe

**An organic result is a citation. An AI Overview is a claim.**

An organic hit carries the URL the address was printed on, so it can be
re-fetched and confirmed — that is the same standard `hook-verifier` holds a
quote to. An AI Overview carries prose, and on the probe that justified this
module it produced `support@fitbridge.ae` for a lead, attributed to a real page
that in fact says `info@`. Plausible local part, real domain, real citation,
address does not exist — the hardest possible fabrication to catch by eye, and
`email-verify` caught it as a hard bounce.

So `provenance` is on every candidate and it is not decoration:

    organic       a URL to re-fetch. Confirmable.
    ai_overview   a claim. Confirm on the cited page or drop it. NEVER adopt.

Nothing here adopts anything either way. Every candidate still goes through
`email-check` and `email-verify`, which is what turned that fabrication into a
FAIL instead of a send.

## The second rule, which cost four false positives to learn

**An address needs a reason to be believed this lead's** — their name in the
local part, a domain already known to be theirs, or a source page that names
them in full. See `_is_corroborated`.

Without it the first live run reported FOUND four times in five, every time on
a stranger's address: an Egyptian pharmaceutical panel, a fitness LLC on
another continent, a Dubai clinic's appointments desk, and a different man
named Spencer. A query about a person returns pages that merely mention them,
and each of those pages had exactly one address on it, so ranking floated it
straight to the top of a verdict callers act on. Uncorroborated addresses are
kept in `unrelated` and counted in the reason, never in `candidates` — a
dropped address should be visible, because the filter is a heuristic and the
count is how anybody would notice it going wrong.

## The absence verdict

`ABSENT` is the capability the free path never had. When an AI Overview says
plainly that no public address exists — "not listed in public directories",
"handled directly through direct messaging" — that is a decision rather than an
empty result: stop paying to look for this lead's address, they are DM-only.

**It is advisory, and it gates spend and never inclusion**, the machine's own
asymmetry. A false ABSENT costs one address; making it a drop would cost a
lead. It requires BOTH a negative phrase AND no organic candidate, because a
model that hedges in prose while the SERP underneath carries the address must
lose to the SERP.
"""

from __future__ import annotations

import re
from typing import Any

from audit.email_check import name_tokens
from audit.urls import registrable_domain

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Provenance for an address the lead published on their own channel. It ranks
# above an organic citation because it settles the question a citation cannot:
# whether this is the right person of that name.
SELF_PUBLISHED = "self_published"

# Local parts that belong to an organisation rather than a person. Shared in
# spirit with email_check._ROLE_LOCALS, kept separate because this list is used
# for a different decision: not "is this a weaker address" but "is this the
# address of the SITE I found it on rather than of the lead".
_ROLE_LOCALS = {
    "info", "contact", "hello", "hi", "support", "admin", "team", "help",
    "office", "mail", "enquiries", "inquiries", "reception", "bookings",
    "booking", "press", "sales", "studio", "newsletter", "media", "billing",
    "accounts", "orders", "careers", "jobs", "privacy", "legal", "webmaster",
    "noreply", "no-reply", "donotreply",
}

# Domains that never carry a lead's address: analytics, CDNs, placeholder text
# in a theme, and the example domains an unedited template ships with. The
# 2026-08-03 probe harvested `johnappleseed@gmail.com` — Apple's placeholder —
# off a real page, so a name that is famously fake is worth naming here.
_JUNK_DOMAINS = {
    "example.com", "example.org", "example.net", "domain.com", "email.com",
    "yourdomain.com", "sentry.io", "wixpress.com", "squarespace.com",
    "godaddy.com", "sentry-next.wixpress.com", "test.com", "email.tld",
}
_JUNK_LOCALS = {"johnappleseed", "john.appleseed", "janedoe", "jane.doe",
                "johndoe", "john.doe", "youremail", "your.email", "email",
                "name", "firstname", "yourname"}

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")

# Phrases an AI Overview uses when it has actually looked and found nothing,
# as opposed to when it simply did not say. Deliberately narrow: each one is a
# statement about availability, not a hedge. "may not be" and "you might try"
# are absent on purpose — a model hedging is not a finding.
_ABSENCE_PATTERNS = (
    r"not (?:publicly )?listed",
    r"not (?:publicly )?available",
    r"no (?:official |public |direct )*e-?mail",
    r"(?:does|do) not (?:publicly )?(?:list|publish|provide)",
    r"is not (?:publicly )?(?:shared|published|disclosed)",
    r"handled (?:directly )?through direct messaging",
    r"only (?:available )?(?:via|through) (?:dm|direct message)",
)
_ABSENCE_RE = re.compile("|".join(_ABSENCE_PATTERNS), re.I)


def build_query(name: str, headline: str = "", location: str = "",
                domains: tuple = ()) -> str:
    """The query shape that worked: who they are, what they do, **the domain
    they are already known to own**, and the words `email address`.

    Haytham's own: `jen de mel Strength & Breath Coaching for Mothers email
    address`. The title matters — a bare name collides, and the probe's
    searches for "Sandra Spencer" returned a Canadian nutritionist and two
    unrelated Spencers.

    **The domain is the term this function shipped without and it cost three
    of five leads.** The first live run built queries from name, headline and
    city alone and came back with nothing for Lana Ave, whose address sits on
    the homepage of `lanawl.com`. The hand-written queries that found four
    addresses all carried a brand term the machine already knew — `fitbridge`,
    `White Antler Group` — because a coach's address is indexed next to their
    business name far more often than next to their positioning line.

    Deduped at the TOKEN level, case-insensitively. Real lists produce
    `Dubai Dubai` from a city that is also in the headline, and
    `Akram Afify AKRAM AFIFY` from a display name that repeats the person's.
    Both were in the first live run. Junk punctuation goes too — a list marks
    an uncertain country as `UAE?`, and the question mark is a search operator
    to nobody and noise to Google."""
    parts = [(name or "").strip()]
    if headline:
        # "Name | Positioning | City" — drop every separator, not just the
        # first, then let the token dedupe below remove the name and the city.
        parts.append(" ".join(re.split(r"\s*[|·•]\s*", headline.strip())))
    if location:
        parts.append(location.strip())
    for dom in domains:
        reg = registrable_domain(dom)
        # A platform URL is not a brand term: `whop.com` would search for Whop.
        if reg and reg not in _NOT_A_BRAND:
            parts.append(reg)
            break
    parts.append("email address")

    seen: set[str] = set()
    out: list[str] = []
    for token in " ".join(p for p in parts if p).split():
        clean = re.sub(r"[^\w.&'-]+", "", token, flags=re.UNICODE).strip("-.'")
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return " ".join(out)


# Hosts that are somebody else's brand, so putting one in a query searches for
# the platform instead of the lead. The link-in-bio and storefront hosts a
# coach's "website" column actually contains.
_NOT_A_BRAND = {
    "whop.com", "linktr.ee", "beacons.ai", "bio.link", "stan.store",
    "milkshake.app", "taplink.cc", "carrd.co", "about.me", "solo.to",
    "linkin.bio", "calendly.com", "typeform.com", "instagram.com",
    "facebook.com", "linkedin.com", "youtube.com", "tiktok.com", "wa.me",
    "t.me", "zoom.us", "google.com", "notion.site", "substack.com",
}


def _clean(addr: str) -> str:
    """Trim an address out of running prose.

    AI Overview text runs sentences together — `jendemel@icloud.com.If you
    need...` — and the address regex happily reads `.If` as another label,
    producing `jendemel@icloud.com.if`, a real-looking address on Iceland's
    TLD that goes to the verifier and comes back a hard bounce.

    Two shapes, and shipping only the first left the second live for one run:

      `...icloud.com.If you`     a whole trailing label in Title Case
      `...icloud.comLocation:`   the next word glued straight onto the TLD

    The first is caught by dropping a Title-Case label — real TLDs are written
    all-lower or all-upper, never `.If`. The second needs a cut inside the
    label at a lowercase-to-uppercase boundary, which `SITE.COM` does not have
    and `comLocation` does. Neither rule alone covers both, which is how
    `jendemel@icloud.comlocation` reached a candidate list."""
    raw = (addr or "").strip().strip(".,;:<>()[]\"'")
    local, at, domain = raw.partition("@")
    if at:
        labels = domain.split(".")
        while len(labels) > 2 and re.fullmatch(r"[A-Z][a-z]+", labels[-1]):
            labels.pop()
        if labels:
            cut = re.search(r"(?<=[a-z])(?=[A-Z])", labels[-1])
            if cut:
                labels[-1] = labels[-1][:cut.start()]
        raw = f"{local}@{'.'.join(l for l in labels if l).rstrip('.')}"
    a = raw.lower()
    if a.endswith(_IMAGE_SUFFIXES) or a.count("@") != 1 or "." not in a.split("@")[1]:
        return ""
    return a


def _is_junk(addr: str) -> bool:
    local, _, domain = addr.partition("@")
    return (domain in _JUNK_DOMAINS or local in _JUNK_LOCALS
            or domain.endswith(".example") or not domain)


def _candidate(addr: str, *, source_url: str, source_title: str,
               provenance: str, tokens: list[str], lead_domains: set[str],
               source_blob: str = "") -> dict:
    """One address with everything a later decision needs, and no decision made."""
    local, _, domain = addr.partition("@")
    host = registrable_domain(source_url) if source_url else ""
    flat_blob = re.sub(r"[^a-z]+", " ", (source_blob or "").lower())
    blob_tokens = set(flat_blob.split())
    return {
        "email": addr,
        "source_url": source_url,
        "source_title": source_title,
        "provenance": provenance,
        "_host": host,
        "name_match": any(t in local.replace(".", "").replace("_", "").replace("-", "")
                          for t in tokens),
        "role_account": local in _ROLE_LOCALS,
        "on_lead_domain": bool(domain) and domain in lead_domains,
        "same_host_as_source": bool(host) and domain == host,
        # EVERY name token, never one. "Spencer" alone matched a page about
        # Spencer Lodge, a different person, on the first live run.
        "source_names_lead": bool(tokens) and all(t in blob_tokens for t in tokens),
        # Is the source page this ADDRESS's own organisation? True when the
        # address domain's stem is named in the page's title or url —
        # `whiteantlergroup.com` cited on a page titled "White Antler Group
        # LLC". Without it, "the page names the lead" corroborated a PAGE
        # rather than an address, and a reel genuinely about Jeff Maingi
        # carried a collaborator's address straight through.
        "source_is_the_orgs_page": bool(domain) and _stem(domain) in re.sub(
            r"[^a-z]+", "", f"{source_title} {source_url}".lower()),
    }


def _stem(domain: str) -> str:
    """`white-antler-group.com` -> `whiteantlergroup`. The comparable form of a
    domain, so it can be looked for in prose and in a url slug alike."""
    return re.sub(r"[^a-z]+", "", (domain or "").rsplit(".", 1)[0].lower())


def _is_corroborated(cand: dict) -> bool:
    """Is there any reason to think this address is THIS lead's?

    Three ways, and a candidate needs one:

      name_match       the local part carries their name (`lana@lanawl.com`)
      on_lead_domain   it is on a domain already known to be theirs
      an org page      the page names them in full AND is that address's own
                       organisation's page — which is how
                       `info@whiteantlergroup.com` qualifies, cited on a
                       LinkedIn page titled "White Antler Group LLC" whose
                       snippet reads "Click here to view Sandra Spencer's
                       profile", at a moment when that domain was not yet
                       known to be hers

    **Without any of this the stage reported FOUND four times out of five on
    strangers' addresses**: an Egyptian pharmaceutical panel, a fitness LLC on
    another continent, a Dubai clinic's appointments desk, and a different man
    named Spencer. Each was the only address on its page, so ranking floated it
    to the top of the one verdict a caller acts on.

    **The third way needs all three conditions and the first cut had two.**
    "The page names them in full" alone re-admitted `andrea@fitqtllc.org` off
    an Instagram reel that genuinely is about Jeff Maingi: a page being about
    somebody corroborates the PAGE, never an address printed on it, because
    collaborators, sponsors and commenters all leave addresses on a person's
    own page. Requiring the address's own domain to be the page's subject is
    what separates a company's contact line from a guest's signature."""
    return (cand["name_match"] or cand["on_lead_domain"]
            or (cand["source_names_lead"] and cand["source_is_the_orgs_page"]))


def _is_the_hosts_own(cand: dict, better_hosts: set[str]) -> bool:
    """A role address on the same domain as the page it sits on is that site's
    own desk — but ONLY when the same page also gave up something better.

    This separates `hello@oxygenadvantage.com`, the accreditation body's
    contact printed on every instructor page, from `jendemel@icloud.com`
    printed beside it. Both came back in one result on the probe.

    **The "something better" condition is the whole rule, and the first cut
    lacked it.** Without it the filter also dropped `info@fitbridge.ae` from
    `fitbridge.ae` — a lead's own site is exactly where their role address
    lives, and a company with one inbox has no name-matched alternative to
    offer. That is the Email OS rule stated as code: generic only if nothing
    better, so a generic address is discarded only once something better
    actually exists. A test caught it; on a real batch it would have looked
    like the lead had no address at all."""
    return (cand["same_host_as_source"] and cand["role_account"]
            and not cand["name_match"] and not cand["on_lead_domain"]
            and cand["_host"] in better_hosts)


def _rank(cand: dict) -> tuple:
    """Most-likely-theirs first. A citation always outranks a claim, because
    only one of the two can be confirmed."""
    return (
        {SELF_PUBLISHED: 0, "organic": 1}.get(cand["provenance"], 2),
        0 if cand["name_match"] else 1,
        0 if cand["on_lead_domain"] else 1,
        0 if not cand["role_account"] else 1,
        cand["email"],
    )


def _organic_rows(item: dict) -> list[dict]:
    rows = item.get("organicResults") or item.get("organic_results") or []
    return [r for r in rows if isinstance(r, dict)]


def _ai_text(item: dict) -> str:
    ao = item.get("aiOverview") or item.get("ai_overview") or {}
    if isinstance(ao, str):
        return ao
    if not isinstance(ao, dict):
        return ""
    for key in ("content", "text", "markdown", "answer"):
        val = ao.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return " ".join(str(v) for v in ao.values() if isinstance(v, str))


def from_observations(name: str, observations, *, lead_domains: tuple = ()) -> list[dict]:
    """The addresses the lead printed on their own channel, for free.

    A coach who wants to be emailed often writes the address in their Instagram
    bio, and it is the best-corroborated address there is: self-published, on a
    channel already confirmed as theirs, with no question of which person of
    that name it belongs to. This module's whole failure mode — a stranger's
    real mailbox that verifies clean — cannot happen here.

    **Measured on `2026-08-03-ig237`.** The SERP found 6 addresses across 23
    leads and 2 of the 4 that survived corroboration were not among them: they
    were sitting in the bio text the dump already carried, and no stage read it.
    `extract` harvests the lead's own *pages* and this list has almost no
    sites; the corpus was the only place those two existed.

    It is a harvest and not a verdict. The address is a candidate a human
    confirms, exactly as a FOUND one is, and it still goes to the verifier.
    """
    tokens = name_tokens(name, min_len=3)
    domains = {registrable_domain(d) for d in lead_domains if d}
    domains.discard("")
    seen, out = set(), []
    for obs in observations or []:
        text = (obs.get("text") if isinstance(obs, dict)
                else getattr(obs, "text", "")) or ""
        url = (obs.get("url") if isinstance(obs, dict)
               else getattr(obs, "url", "")) or ""
        for raw in _EMAIL_RE.findall(text):
            addr = _clean(raw)
            if not addr or _is_junk(addr) or addr in seen:
                continue
            seen.add(addr)
            cand = _candidate(addr, source_url=url, source_title="",
                              provenance=SELF_PUBLISHED, tokens=tokens,
                              lead_domains=domains, source_blob=text)
            out.append(cand)
    return sorted(out, key=_rank)


def find_addresses(name: str, item: dict, *, lead_domains: tuple = ()) -> dict:
    """Turn ONE search result item into ranked, provenanced address candidates.

    `item` is a single Google-Search-Scraper dataset record (or anything with
    the same `organicResults` / `aiOverview` shape). `lead_domains` are domains
    already known to be this lead's — their site, their bio links — which
    promotes an address on one of them without being required.

    Returns:
      {"verdict": "FOUND"|"CLAIMED"|"ABSENT"|"NONE",
       "candidates": [ ... ranked ... ],
       "absence_note": <str>,     # the AI Overview's own words, on ABSENT
       "reason": <str>}

    FOUND    at least one organic citation. The only verdict carrying a URL
             that can be re-fetched.
    CLAIMED  only an AI Overview said so. Confirm on the cited page or drop —
             this is the verdict that fabricated an address on the probe.
    ABSENT   no candidate, and the AI Overview stated there is no public
             address. Advisory, gates spend and never inclusion.
    NONE     nothing found and nothing said. Not the same as ABSENT, and the
             difference is the whole reason the AI Overview is worth $0.002.
    """
    tokens = [t for t in name_tokens(name or "", min_len=3)]
    domains = {registrable_domain(d) for d in lead_domains if d}
    domains.discard("")

    seen: set[str] = set()
    cands: list[dict] = []

    for row in _organic_rows(item):
        url = row.get("url") or ""
        title = row.get("title") or ""
        blob = " ".join(str(row.get(k) or "") for k in
                        ("title", "description", "snippet", "displayedUrl", "url"))
        for raw in _EMAIL_RE.findall(blob):
            addr = _clean(raw)
            if not addr or _is_junk(addr) or addr in seen:
                continue
            seen.add(addr)
            cands.append(_candidate(addr, source_url=url, source_title=title,
                                    provenance="organic", tokens=tokens,
                                    lead_domains=domains, source_blob=blob))

    # Which source pages gave up something better than their own front desk.
    # Computed over the whole result set rather than per row, because the two
    # addresses on the probe's directory page arrived in one snippet.
    better_hosts = {c["_host"] for c in cands
                    if c["_host"] and (c["name_match"] or c["on_lead_domain"])}
    cands = [c for c in cands if not _is_the_hosts_own(c, better_hosts)]

    unrelated = [c for c in cands if not _is_corroborated(c)]
    cands = [c for c in cands if _is_corroborated(c)]

    ai_text = _ai_text(item)
    for raw in _EMAIL_RE.findall(ai_text):
        addr = _clean(raw)
        if not addr or _is_junk(addr) or addr in seen:
            continue
        seen.add(addr)
        cands.append(_candidate(addr, source_url="", source_title="AI Overview",
                                provenance="ai_overview", tokens=tokens,
                                lead_domains=domains))

    cands.sort(key=_rank)
    dropped = (f"; {len(unrelated)} address(es) on pages that merely mention "
               f"this lead were dropped as somebody else's" if unrelated else "")

    if any(c["provenance"] == "organic" for c in cands):
        top = cands[0]
        return {"verdict": "FOUND", "candidates": cands, "unrelated": unrelated,
                "absence_note": "",
                "reason": f"{len(cands)} candidate(s), best is {top['email']} "
                          f"cited on {top['source_url'] or 'an unnamed page'}{dropped}"}

    if cands:
        return {"verdict": "CLAIMED", "candidates": cands, "unrelated": unrelated,
                "absence_note": "",
                "reason": f"{len(cands)} candidate(s) from the AI Overview only — "
                          f"confirm on the cited page before any use, never "
                          f"adopt{dropped}"}

    hit = _ABSENCE_RE.search(ai_text or "")
    if hit:
        sentence = _absence_sentence(ai_text, hit.start())
        return {"verdict": "ABSENT", "candidates": [], "unrelated": unrelated,
                "absence_note": sentence,
                "reason": "the AI Overview states no public address exists — "
                          f"advisory, stop spending on this lead's address{dropped}"}

    return {"verdict": "NONE", "candidates": [], "unrelated": unrelated,
            "absence_note": "",
            "reason": f"no address in the results and nothing said about there "
                      f"being none{dropped}"}


def _absence_sentence(text: str, at: int) -> str:
    """The sentence the absence phrase sits in, so the report quotes the
    overview rather than paraphrasing it — the same reason `observe` keeps
    text verbatim."""
    start = max(text.rfind(".", 0, at), text.rfind("\n", 0, at)) + 1
    end = text.find(".", at)
    end = len(text) if end == -1 else end + 1
    return " ".join(text[start:end].split())[:300]


def print_find(name: str, item: dict, *, lead_domains: tuple = ()) -> int:
    """One quotable gate line, same contract as the other email commands.

    Exit 0 on FOUND and on ABSENT — a confirmed absence is an answer, not a
    failure, and the machine has always held that a null result reached
    honestly is a good one. Exit 1 on CLAIMED and NONE, which are both "there
    is more to do here"."""
    r = find_addresses(name, item, lead_domains=lead_domains)
    line = f"EMAIL FIND: {r['verdict']} — {name or '(no name)'}: {r['reason']}"
    if r["absence_note"]:
        line += f' ["{r["absence_note"]}"]'
    print(line)
    for c in r["candidates"][:5]:
        flags = ",".join(f for f, on in (
            ("name-match", c["name_match"]), ("own-domain", c["on_lead_domain"]),
            ("org-page", c["source_names_lead"] and c["source_is_the_orgs_page"]),
            ("role", c["role_account"])) if on) or "no flags"
        src = c["source_url"] or "AI Overview, no page"
        print(f"    {c['provenance']:<12} {c['email']:<38} {flags} — {src}")
    return 0 if r["verdict"] in ("FOUND", "ABSENT") else 1
