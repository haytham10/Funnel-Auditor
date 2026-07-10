"""
Evidence packet builder.

Takes a CrawlResult, runs every check + extraction over each page, evaluates
the machine-checkable floors, flags leak *candidates* (mapped to the 5-stop
walk's known patterns), and writes a self-contained packet:

    evidence/<slug>/
        evidence.json     — full structured output
        packet.md         — the paste-ready walk packet for the opener-finder
        pages/<n>_<slug>.txt  — visible text per page
        screenshots/      — desktop + mobile PNG per page

The packet is a FIRST DRAFT of the walk, machine half only. The sting test,
vitamin filter, lane call, and anything behind logins/DMs/payments stay with
the human + Claude layer.

Candidate rules that keep the packet honest:
- Findings on EXTERNAL pages (booking platforms aside) are never her leaks.
- A stale date repeated by a shared nav/footer widget is ONE finding that
  appears on N pages, not N findings.
- An offer page that says "coming soon" / "sold out" / "fully booked" /
  "temporarily unavailable" is an empty-shelf candidate — the single
  highest-value machine catch (it's copy, so no link ever breaks).
- Blog publish dates are a soft "quiet blog" signal, not the Pam pattern.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from audit.crawler import CrawlResult, CrawledPage
from audit.checks import (
    check_pixels, check_forms, check_links, check_meta, check_speed, check_checkout,
)
from audit.extract import (
    visible_text, extract_headings, extract_prices, extract_emails,
    extract_dates, extract_availability,
)
from audit.gates import evaluate_floors
from audit.urls import same_site, slugify
from audit import vision_gate
from config import BOOKING_EMBED_HOSTS, JS_BUTTON_NOISE_RE

_BOOKING_EMBED_RE = re.compile(
    "|".join(re.escape(h) for h in BOOKING_EMBED_HOSTS), re.I
)
_JS_BUTTON_NOISE_RE = re.compile(JS_BUTTON_NOISE_RE, re.I)


def _detect_booking_embed(html: str) -> str:
    """Inline booking widgets (Calendly and friends) are a confirmed
    screenshot blind spot: the widget's iframe loads async and its own
    slot-availability fetch can land after the screenshot is taken, so a
    real, working booking widget can show up as blank space in the
    evidence screenshot. Flag the platform by name whenever its marker
    (script src / data-url / iframe src) appears anywhere in the page HTML,
    so a blank area near this page is read as 'screenshot unreliable here',
    never as a confirmed missing-CTA finding."""
    m = _BOOKING_EMBED_RE.search(html)
    return m.group(0).lower() if m else ""


def _interactive_blind_spots(html: str) -> dict:
    """The Calendly miss was one instance of a bigger category: ANY iframe
    (chat widgets, other schedulers, Stripe/PayPal payment elements on a
    checkout page, maps, video) can carry real functionality a screenshot
    isn't guaranteed to paint, and ANY button with no href is a JS-only
    control whose destination a static crawl can't follow. Inventory both
    directly from the rendered DOM — independent of whether anything
    painted visually — so a blank-looking area always has a structural
    cross-check instead of resting on pixels alone."""
    soup = BeautifulSoup(html, "html.parser")

    iframes = []
    for tag in soup.select("iframe[src]"):
        src = (tag.get("src") or "").strip()
        if not src or src.startswith("about:blank") or src.startswith("javascript"):
            continue
        iframes.append({"src": src, "known_booking_platform": bool(_BOOKING_EMBED_RE.search(src))})

    js_only_buttons = []
    for tag in soup.select("button"):
        if tag.find_parent("a[href]"):
            continue
        text = tag.get_text(separator=" ", strip=True)
        if not text or len(text) > 80:
            continue
        # Nav toggles and FAQ/accordion questions are near-universal UI
        # chrome, not funnel-relevant destinations — flagging every one of
        # them buries the buttons that actually matter in noise.
        if _JS_BUTTON_NOISE_RE.search(text) or text.rstrip().endswith("?"):
            continue
        js_only_buttons.append(text[:60])

    return {"iframes": iframes, "js_only_buttons": js_only_buttons[:20]}

# How much page text goes inline in packet.md. 700 chars was cutting every
# offer/course/checkout page off after its hero section — exactly the part
# of the page that never has the actual curriculum, pricing structure, or
# copy inconsistencies in it. A manual walk caught a sales-page-vs-checkout
# curriculum mismatch on Heidi McBain (Modules One-Eight vs Part One-Five)
# that the tool couldn't have surfaced at 700 chars — that content starts
# well past that cutoff. Offer-bearing pages now get the full page text
# inline (still capped, matching the file cap); everything else gets a
# shorter preview since About/Contact pages rarely carry findings.
TEXT_INLINE_CHARS = 700
TEXT_INLINE_CHARS_OFFER = 6000
TEXT_FILE_MAX_CHARS = 20000   # cap per page text file

_OFFER_PAGE_TYPES = ("sales", "course", "checkout", "booking", "freebie", "opt-in")


def _inline_cap(link_type: str) -> int:
    return TEXT_INLINE_CHARS_OFFER if link_type in _OFFER_PAGE_TYPES else TEXT_INLINE_CHARS


@dataclass
class PageEvidence:
    page: CrawledPage
    checks: dict = field(default_factory=dict)
    headings: list = field(default_factory=list)
    prices: list = field(default_factory=list)
    emails: dict = field(default_factory=dict)
    dates: list = field(default_factory=list)
    availability: list = field(default_factory=list)
    text: str = ""
    text_file: str = ""
    booking_embed: str = ""
    blind_spots: dict = field(default_factory=dict)


_slug = slugify  # kept as a local alias — this module's callers use _slug()


# On bio-link platforms, "same host" links are other people's profiles and
# platform marketing pages — not the lead's own funnel. Her actual links get
# crawled directly, which is the real dead-link test.
_BIO_HOSTS = ("linktr.ee", "linktree.com", "stan.store", "beacons.ai")


def _is_bio_host(url: str) -> bool:
    host = urlparse(url).netloc.lower().lstrip("www.")
    return any(host == h or host.endswith("." + h) for h in _BIO_HOSTS)


def _analyze_page(page: CrawledPage, seed_url: str, lead_name: str) -> PageEvidence:
    ev = PageEvidence(page=page)
    if not page.html:
        return ev
    html, url = page.html, page.url
    skip_links = _is_bio_host(url) or page.external
    ev.checks = {
        "pixels": check_pixels(html, url),
        "forms": check_forms(html, url),
        "links": ({"broken": [], "unverifiable": [], "total_checked": 0, "skipped": True}
                  if skip_links else check_links(html, url)),
        "meta": check_meta(html, url),
        "speed": check_speed(html, url, page.load_time_ms),
        "checkout": check_checkout(html, url),
    }
    ev.text = visible_text(html)
    ev.headings = extract_headings(html)
    ev.prices = extract_prices(ev.text)
    ev.emails = extract_emails(html, url, seed_url=seed_url, lead_name=lead_name)
    ev.dates = extract_dates(ev.text, page_url=url)
    ev.availability = extract_availability(ev.text)
    ev.booking_embed = _detect_booking_embed(html)
    ev.blind_spots = _interactive_blind_spots(html)
    return ev


# ---------------------------------------------------------------------------
# Machine-flagged leak candidates (mapped to walk.md known patterns)
# ---------------------------------------------------------------------------

def _leak_candidates(pages: list[PageEvidence], seed_url: str) -> list[dict]:
    """
    Conservative auto-flags. Every one is a CANDIDATE: the sting test and
    vitamin filter still decide whether it's an opener. Tiers follow the
    known patterns in the opener-finder's walk.md.
    """
    cands: list[dict] = []

    def add(stop, tier, what, where, note=""):
        cands.append({"stop": stop, "tier": tier, "what": what, "where": where, "note": note})

    own_pages = [p for p in pages if not p.page.external]

    any_capture = any(
        p.checks.get("forms", {}).get("form_present") for p in own_pages
    )

    # --- Stale dates, deduped across pages (shared nav/footer widgets) ---
    stale_seen: dict[str, dict] = {}
    for p in own_pages:
        for d in p.dates:
            if not d["stale_candidate"]:
                continue
            key = d["raw"] + "|" + d["context"][:60]
            if key in stale_seen:
                stale_seen[key]["pages"].append(p.page.url)
            else:
                stale_seen[key] = {"date": d, "pages": [p.page.url]}
    for entry in list(stale_seen.values())[:4]:
        d = entry["date"]
        n = len(entry["pages"])
        where = entry["pages"][0] + (f" (+{n - 1} more pages — shared nav/footer element)" if n > 1 else "")
        add(3, "B", f"Stale date still showing: \"{d['raw']}\" ({d['days_past']} days past)",
            where,
            f"Context: …{d['context'][:140]}… (Pam pattern — passed kickoff date reads as 'I missed it'.)"
            + (" YEAR ASSUMED — could mean next occurrence, verify." if d["year_assumed"] else ""))

    # --- Offer availability: the empty-shelf pattern ---
    avail_seen: set[str] = set()
    for p in own_pages:
        pg = p.page
        offer_page = pg.link_type in _OFFER_PAGE_TYPES or bool(p.prices)
        for a in p.availability:
            key = a["kind"] + "|" + a["context"][:50]
            if key in avail_seen:
                continue
            avail_seen.add(key)
            if a["kind"] == "placeholder":
                add(3, "B", f"Placeholder text still live: \"{a['match']}\"", pg.url,
                    f"Context: …{a['context'][:140]}… Shipped-unfinished signal, same family as a stale date.")
            elif a["kind"] == "waitlist_only":
                continue  # only meaningful in combination — judged below
            elif offer_page:
                tier = "A" if a["kind"] in ("unavailable", "fully_booked", "closed") else "B"
                add(3, tier,
                    f"Offer availability blocker on an offer page: \"{a['match']}\"", pg.url,
                    f"Context: …{a['context'][:140]}… If this is the ladder's entry offer, "
                    "warmed-up traffic has nowhere to buy in — verify what a visitor can actually purchase today.")

    for p in own_pages:
        pg = p.page
        if pg.link_type == "bio_page" and pg.error:
            if pg.http_status == 200:
                add(1, "-", "Bio page blocked the headless crawl (HTTP probe: 200)", pg.url,
                    "Site is UP for real visitors — bot wall, not a finding. Walk it by hand/screenshots.")
            else:
                add(1, "A", "Bio link fails to load", pg.url,
                    f"Error: {pg.error[:100]}. HTTP probe: {pg.http_status or 'no response'}. "
                    "Verify logged-out: hard 404 = openable, permission wall = not.")

        broken = p.checks.get("links", {}).get("broken", [])
        if broken:
            urls = ", ".join(f"{b['url']} ({b['status'] or 'no response'})" for b in broken[:4])
            add("-", "B", f"{len(broken)} dead internal link(s)", pg.url,
                f"Dead: {urls}. Dead/stale element — the finding type behind most warm replies. "
                "Verify logged-out by hand before opening on it.")

        if pg.link_type in ("freebie", "opt-in") and not pg.error:
            if not p.checks.get("forms", {}).get("form_present"):
                note = "If it delivers without capturing a contact, downloaders who don't buy now are gone."
                if _is_bio_host(pg.url):
                    note += (" CAUTION: Stan/Linktree collect the email inside the order overlay, "
                             "which a crawl can't see — verify by hand before opening on this.")
                add(2, "B", "Freebie/opt-in page with no email capture visible", pg.url, note)

        if pg.link_type == "checkout":
            if pg.error and pg.http_status != 200:
                add(4, "A", "Checkout page fails to load", pg.url,
                    f"Error: {pg.error[:100]}")
            elif not pg.error:
                co = p.checks.get("checkout", {})
                # Only her own transacting checkout counts — an order bump
                # missing from her web designer's cart is not her leak.
                if (same_site(pg.url, seed_url) and co.get("transacts")
                        and co.get("platform") == "kajabi"
                        and not co.get("order_bump_detected")):
                    add(4, "B", "Bare Kajabi checkout — no order bump detected", pg.url,
                        "Easiest revenue lift at the highest-intent moment (PWH receipt: $522 from one bump).")

    # --- Quiet blog: soft signal, never a leak candidate ---
    for p in own_pages:
        blog_dates = [d for d in p.dates if d.get("blog_byline") and 60 < d["days_past"] < 400]
        if blog_dates and re.search(r"/(blog|news|articles)(/|$)", p.page.url, re.I):
            newest = min(blog_dates, key=lambda d: d["days_past"])
            add("-", "C", f"Blog looks quiet — newest post ~{newest['days_past']} days old", p.page.url,
                "Soft activity signal only. Cross-check against her IG activity before reading anything into it.")
            break

    if own_pages and not any_capture:
        add(5, "C", "No email capture anywhere in the crawled funnel", "whole funnel",
            "Audience ownership signal. MECHANISM by default — only an opener if framed as felt cost.")

    return cands


# ---------------------------------------------------------------------------
# The 5-stop walk — mandatory, logged, never silently skipped.
#
# Every audit must report a result for all five stops (found / not_found /
# blocked), even when the answer is "nothing here." A blank stop is a bug,
# not a clean result — it means the walk stopped early instead of reporting
# what it actually found.
# ---------------------------------------------------------------------------

_START_HERE_RE = re.compile(r"\bstart here\b|\bbegin\b|\bstart now\b|\bget started\b", re.I)


def _stop_bio(pages: list[PageEvidence], funnel_links: list[dict]) -> dict:
    bio = pages[0] if pages else None
    if not bio or not bio.page.html:
        err = bio.page.error if bio else "no crawl"
        return {"stop": "bio", "status": "blocked",
                "detail": f"Bio page failed to load ({err[:120] if err else 'unknown error'})."}
    n = len(funnel_links)
    detail = f"{n} destination link(s) found on the bio page."
    if n >= 4 and not any(_START_HERE_RE.search(l.get("label", "")) for l in funnel_links):
        detail += (f" {n} near-equal links, none labeled as a primary entry point "
                   "(\"Start Here\"/\"Begin\") — ambiguous first click for a new visitor.")
    return {"stop": "bio", "status": "found", "detail": detail}


def _stop_freebie(pages: list[PageEvidence]) -> dict:
    freebies = [p for p in pages if p.page.link_type in ("freebie", "opt-in") and not p.page.error]
    if not freebies:
        return {"stop": "freebie", "status": "not_found",
                "detail": "No freebie/opt-in page found anywhere in the crawled funnel."}
    captured = [p for p in freebies if p.checks.get("forms", {}).get("form_present")]
    if captured:
        return {"stop": "freebie", "status": "found",
                "detail": f"{captured[0].page.url} — captures email before delivering."}
    return {"stop": "freebie", "status": "found",
            "detail": f"{freebies[0].page.url} — no visible email capture form; "
                      "delivers without capturing a contact, or capture happens off-page "
                      "(verify by hand before opening on this)."}


def _stop_offer(pages: list[PageEvidence]) -> dict:
    # Category classification is a heuristic guess and imperfect — a real
    # price on the page is a stronger, direct signal than the URL/label
    # keyword match that assigns link_type. A page priced at $2,700 but
    # classified "direct" (no "sales"/"course" keyword in its slug) is
    # still an offer page.
    offers = [p for p in pages if not p.page.error and not p.page.external
              and p.page.link_type != "checkout"
              and (p.page.link_type in ("sales", "course") or p.prices)]
    if not offers:
        return {"stop": "offer", "status": "not_found",
                "detail": "No priced offer/sales page found on her own site."}
    lines = []
    for p in offers[:3]:
        price = p.prices[0]["price"] if p.prices else "no price shown"
        lines.append(f"{p.page.url} — {price}")
    return {"stop": "offer", "status": "found", "detail": "; ".join(lines)}


def _stop_checkout(pages: list[PageEvidence]) -> dict:
    checkouts = [p for p in pages if p.page.link_type == "checkout"]
    lines = []
    any_loaded = False
    for p in checkouts[:3]:
        if p.page.error:
            lines.append(f"{p.page.url} — FAILED TO LOAD ({p.page.error[:100]})")
            continue
        any_loaded = True
        price = p.prices[0]["price"] if p.prices else "no price shown"
        transacts = p.checks.get("checkout", {}).get("transacts")
        state = "requires purchase to go further" if transacts else "reached, no payment form on this page"
        lines.append(f"{p.page.url} — {price} — blocked: {state}")
    if lines:
        return {"stop": "checkout", "status": "found" if any_loaded else "blocked",
                "detail": "; ".join(lines)}

    # No separate checkout URL — some platforms (Squarespace commerce
    # blocks, embedded Stripe elements) transact inline on the sales page
    # itself instead of hopping to a dedicated checkout URL. Missing this
    # is the exact failure that made Nina Bradley's "Pay & book now" flow
    # read as "checkout not reached" when it was actually right there.
    #
    # Requires an actual visible price, not just the word "payment" —
    # Shermon Sims's GoHighLevel privacy-policy page ("Payment information
    # via third-party processors...") matched the transacts regex with no
    # price anywhere on the page, which isn't a checkout, it's a privacy
    # disclosure describing payment processing in the abstract.
    embedded = [p for p in pages if p.page.link_type in ("sales", "course")
                and not p.page.error and p.prices
                and p.checks.get("checkout", {}).get("transacts")]
    if embedded:
        p = embedded[0]
        price = p.prices[0]["price"] if p.prices else "no price shown"
        return {"stop": "checkout", "status": "found",
                "detail": f"{p.page.url} — {price} — embedded checkout on the sales page itself "
                         "(no separate checkout URL to hop to) — blocked: requires purchase to go further"}

    return {"stop": "checkout", "status": "not_reached",
            "detail": "No checkout page reached and no embedded/inline checkout detected on any "
                     "sales or course page — no buy/enroll/reserve link or payment form found "
                     "anywhere in this crawl."}


def _stop_audience(email_capture_anywhere: bool, pages: list[PageEvidence]) -> dict:
    if email_capture_anywhere:
        return {"stop": "audience", "status": "found",
                "detail": "Email capture found — owns at least one list-building mechanism, "
                         "not fully dependent on rented reach."}
    return {"stop": "audience", "status": "not_found",
            "detail": "No email capture found anywhere in the crawled funnel — audience "
                     "appears fully rented (IG/social only), no owned list."}


def _walk_stops(pages: list[PageEvidence], funnel_links: list[dict], email_capture_anywhere: bool) -> list[dict]:
    return [
        _stop_bio(pages, funnel_links),
        _stop_freebie(pages),
        _stop_offer(pages),
        _stop_checkout(pages),
        _stop_audience(email_capture_anywhere, pages),
    ]


# ---------------------------------------------------------------------------
# Cross-stop reconciliation — the primary output, not an afterthought.
#
# A stale cohort date, a price change, or a dropped curriculum section is
# often invisible on any ONE page — a sales page's "reserve your seat" copy
# reads as fine on its own; the leak only exists in the gap between what the
# sales page promises and what checkout actually shows. This is exactly what
# per-page checks structurally cannot catch, no matter how deep they read
# a single page. This pass runs after every page is analyzed and diffs
# Stop 3 (offer) against Stop 4 (checkout) directly, plus checks every date
# anywhere in the funnel against today regardless of which stop it's on.
# ---------------------------------------------------------------------------

def _normalize_price(raw: str) -> str:
    """$59 and $59.00 are the same price. Strip everything but the currency
    symbol/code and the numeric value, drop a trailing .00, so formatting
    differences don't read as a price change."""
    m = re.match(r"([$£€]|USD|AED|GBP|EUR)?\s?([\d,]+(?:\.\d{1,2})?)", raw.strip())
    if not m:
        return raw.strip()
    symbol, number = m.group(1) or "", m.group(2).replace(",", "")
    if number.endswith(".00"):
        number = number[:-3]
    return f"{symbol}{number}"


def _origin_offer_page(checkout: PageEvidence, by_url: dict[str, PageEvidence]) -> PageEvidence | None:
    """Walk a checkout page's hop chain back to the specific sales/course
    page that actually linked to it — NOT just any offer page found
    anywhere on the site. Comparing a checkout against every offer page on
    the domain produced nonsense (a $17 digital-download page "mismatching"
    a $297 course's checkout — they're different products). Only the page
    that was the real click-through source is a valid comparison."""
    seen: set[str] = set()
    current = checkout
    for _ in range(6):
        src = current.page.source_url
        if not src or src in seen:
            return None
        seen.add(src)
        origin = by_url.get(src)
        if origin is None:
            return None
        if origin.page.link_type != "checkout":
            return origin
        current = origin
    return None


def _reconcile(pages: list[PageEvidence]) -> list[dict]:
    findings: list[dict] = []
    own = [p for p in pages if not p.page.error]
    by_url = {p.page.url: p for p in own}
    checkouts = [p for p in own if p.page.link_type == "checkout"]

    # Pair each checkout with the ONE offer page that actually led to it
    # (via the crawl's hop chain), not every offer page on the site.
    pairs: list[tuple[PageEvidence, PageEvidence]] = []
    for c in checkouts:
        origin = _origin_offer_page(c, by_url)
        if origin is not None:
            pairs.append((origin, c))

    for o, c in pairs:
        # A date shown only at checkout, never on the specific offer page
        # that led there — the visitor had no way to know until the last step.
        offer_dates = {d["raw"] for d in o.dates}
        for d in c.dates:
            if not d["stale_candidate"] or d["raw"] in offer_dates:
                continue
            findings.append({
                "kind": "checkout_reveals_stale_date",
                "tier": "A",
                "summary": f"Checkout shows \"{d['raw']}\" ({d['days_past']} days past) that the "
                          "offer page leading here never mentions",
                "where": f"{o.page.url} → {c.page.url}",
                "note": f"The sales page makes no date commitment a visitor could check in advance; "
                       f"checkout is the first and only place the (already-passed) date shows up — "
                       f"…{d['context'][:160]}…",
            })

        # Price mismatch, same product only (paired via the actual hop,
        # not a same-domain scan) — and normalized so "$59" vs "$59.00"
        # doesn't read as a change.
        o_prices = {_normalize_price(p["price"]) for p in o.prices[:5]}
        c_prices = {_normalize_price(p["price"]) for p in c.prices[:5]}
        if o_prices and c_prices and o_prices.isdisjoint(c_prices):
            findings.append({
                "kind": "price_mismatch",
                "tier": "A",
                "summary": f"Price differs between the offer page ({', '.join(sorted(o_prices))}) "
                          f"and its own checkout ({', '.join(sorted(c_prices))})",
                "where": f"{o.page.url} → {c.page.url}",
                "note": "Same product, hop-verified (this checkout was reached FROM this offer page) — "
                       "if this holds up on a manual look, that's the felt cost (someone who saw the "
                       "offer price and returns to buy sees a different number).",
            })

    # Curriculum/section-count comparison — observational only, same-product
    # pairing only. The exact false-positive this guards against: Heidi
    # McBain's sales page called its 8 sections "Modules" and Thinkific's
    # own template called the same 8 sections "Parts" — identical content,
    # cosmetic labels. Only surface when counts differ by 2+, and always as
    # a non-definitive note the human/Claude layer has to read, never as an
    # asserted leak.
    _SECTION_RE = re.compile(
        r"\b(?:Module|Part|Chapter|Session)\s+(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+)\b[:\-]",
        re.I,
    )
    for o, c in pairs:
        o_count = len(set(_SECTION_RE.findall(o.text)))
        c_count = len(set(_SECTION_RE.findall(c.text)))
        if not o_count or not c_count or abs(o_count - c_count) < 2:
            continue
        findings.append({
            "kind": "curriculum_count_note",
            "tier": "C",
            "summary": f"Section count differs: offer page shows ~{o_count}, "
                      f"checkout shows ~{c_count} (observational, not asserted as a leak)",
            "where": f"{o.page.url} → {c.page.url}",
            "note": "Read both pages before opening on this — could be identical content "
                   "under different labels (Module vs Part), a 'Show more' pagination "
                   "artifact, or a genuine drift. Do not treat the count alone as proof.",
        })

    return findings


# ---------------------------------------------------------------------------
# Packet writer
# ---------------------------------------------------------------------------

def build_evidence(
    result: CrawlResult,
    out_dir: str | Path,
    lead_name: str = "",
    handle: str = "",
    followers: int | None = None,
) -> Path:
    """Analyze a CrawlResult and write the evidence packet. Returns packet dir."""
    out = Path(out_dir)
    (out / "pages").mkdir(parents=True, exist_ok=True)

    pages = [_analyze_page(p, result.seed_url, lead_name) for p in result.pages]

    # Page text files
    for i, p in enumerate(pages, start=1):
        if not p.text:
            continue
        fname = f"{i}_{_slug(p.page.url)}.txt"
        (out / "pages" / fname).write_text(p.text[:TEXT_FILE_MAX_CHARS])
        p.text_file = f"pages/{fname}"

    # Floors
    bio = pages[0].page if pages else None
    offer_evidence: list[str] = []
    for p in pages:
        if p.page.error or p.page.external:
            continue
        if p.page.link_type in ("sales", "course", "checkout", "booking"):
            offer_evidence.append(f"{p.page.link_type} page: {p.page.url}")
        for pr in p.prices[:2]:
            offer_evidence.append(f"price {pr['price']} on {p.page.url}")
    floors = evaluate_floors(
        bio_link_alive=bool(bio and not bio.error),
        bio_link_error=(bio.error if bio else "no crawl"),
        offer_evidence=offer_evidence,
        email_capture_anywhere=any(
            p.checks.get("forms", {}).get("form_present")
            for p in pages if not p.page.external
        ),
        followers=followers,
    )

    candidates = _leak_candidates(pages, result.seed_url)
    email_capture_anywhere = any(
        p.checks.get("forms", {}).get("form_present") for p in pages if not p.page.external
    )
    walk_stops = _walk_stops(pages, result.funnel_links, email_capture_anywhere)
    reconciliation = _reconcile(pages)

    # Harvested emails, merged (name-matching personals first)
    personal, generic = [], []
    seen_addr: set[str] = set()
    for p in pages:
        for bucket, target in (("personal", personal), ("generic", generic)):
            for e in p.emails.get(bucket, []):
                if e["email"] not in seen_addr:
                    seen_addr.add(e["email"])
                    target.append(e)
    personal.sort(key=lambda e: not e.get("name_match"))

    evidence = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "lead_name": lead_name,
        "handle": handle,
        "followers": followers,
        "seed_url": result.seed_url,
        "bio_platform": result.platform,
        "floors": floors.as_dict(),
        "walk_stops": walk_stops,
        "reconciliation": reconciliation,
        "harvested_emails": {"personal": personal, "generic": generic},
        "leak_candidates": candidates,
        "funnel_links": result.funnel_links,
        "noise_links": result.noise_links,
        "external_refs": result.external_refs,
        "pages": [
            {
                "url": p.page.url,
                "title": p.page.title,
                "link_type": p.page.link_type,
                "depth": p.page.depth,
                "source_url": p.page.source_url,
                "error": p.page.error,
                "http_status": p.page.http_status,
                "external": p.page.external,
                "load_time_ms": p.page.load_time_ms,
                "screenshot_desktop": p.page.screenshot_desktop,
                "screenshot_mobile": p.page.screenshot_mobile,
                "text_file": p.text_file,
                "text_inline": p.text[:_inline_cap(p.page.link_type)],
                "headings": p.headings,
                "prices": p.prices,
                "emails": p.emails,
                "dates": p.dates,
                "availability": p.availability,
                "checks": p.checks,
                "booking_embed": p.booking_embed,
                "blind_spots": p.blind_spots,
                "cta_clicks": p.page.cta_clicks,
            }
            for p in pages
        ],
    }
    (out / "evidence.json").write_text(json.dumps(evidence, indent=2, default=str))
    (out / "packet.md").write_text(_render_packet(evidence))

    # Vision-pass manifest — built from this same evidence.json plus whatever
    # is already sitting in out/ig/ (IG screenshots are downloaded in the
    # skill's Step 0, before this crawl runs). Re-running this after IG
    # images arrive later is safe: init_manifest() preserves any images
    # already marked read. See audit/vision_gate.py for why this exists —
    # short version: a free-text "I read the screenshots" claim can't be
    # checked, a manifest with a mark-per-file requirement can.
    vision_gate.init_manifest(out)

    return out


def _render_packet(ev: dict) -> str:
    L: list[str] = []
    name = ev["lead_name"] or ev["seed_url"]
    L.append(f"# Funnel Walk Evidence — {name}")
    meta = [f"Generated {ev['generated']}", f"Seed: {ev['seed_url']}", f"Bio platform: {ev['bio_platform']}"]
    if ev["handle"]:
        meta.append(f"Handle: {ev['handle']}")
    if ev["followers"] is not None:
        meta.append(f"Followers: {ev['followers']:,}")
    L.append(" • ".join(meta))
    L.append("")
    L.append("> Machine half of the walk only. Human observations outrank everything here. "
             "Every flag below is a CANDIDATE — sting test and vitamin filter still apply.")

    # Booking-embed screenshot warning — confirmed blind spot (see
    # _detect_booking_embed). Surfaced at the top so it can't be missed.
    embed_pages = [p for p in ev["pages"] if p.get("booking_embed")]
    if embed_pages:
        L.append("\n## ⚠️ SCREENSHOT RELIABILITY WARNING")
        L.append("The following page(s) embed an inline booking widget "
                 "(Calendly or similar). These widgets load async and can appear "
                 "as blank space in the screenshot even when a real, working "
                 "booking option is there. **Do not treat blank space on these "
                 "pages as a missing-CTA finding without checking the raw page "
                 "text/HTML for the widget marker first, and ideally opening the "
                 "live page by hand.**")
        for p in embed_pages:
            L.append(f"- {p['url']} — embed marker: `{p['booking_embed']}`")

    # CTA click-discovery — sales/course/booking pages only (see
    # _discover_cta_destinations). These buttons were actually clicked, so
    # their destination is CONFIRMED, not a guess — read this before
    # treating any of them as an unverified blind spot below.
    click_pages = [p for p in ev["pages"] if p.get("cta_clicks")]
    if click_pages:
        L.append("\n## CTA click-discovery (buttons actually clicked, destinations confirmed)")
        for p in click_pages:
            L.append(f"- {p['url']}:")
            for c in p["cta_clicks"]:
                dest = c["destination"]
                if dest == "navigation":
                    L.append(f"  - \"{c['button_text']}\" → navigates to {c['url']}")
                elif dest == "embedded_widget":
                    srcs = ", ".join(c.get("iframe_src") or []) or "unknown src"
                    L.append(f"  - \"{c['button_text']}\" → reveals an embedded widget ({srcs})")
                elif dest == "no_visible_change":
                    L.append(f"  - \"{c['button_text']}\" → clicked, no visible change detected "
                             "(could be a JS action a static check can't see, e.g. adding to a cart)")
                elif dest == "skipped_unsafe":
                    L.append(f"  - \"{c['button_text']}\" → NOT clicked (reads as a payment/order "
                             "completion action — verify by hand)")

    # Broader blind spots: any iframe (not just known booking platforms) and
    # any JS-only button are both invisible to link extraction and NOT
    # guaranteed to render in the screenshot. Same "verify before calling it
    # missing" rule applies. Buttons already resolved by click-discovery
    # above are excluded here — they're confirmed, not unverified.
    other_iframe_pages = [
        p for p in ev["pages"]
        if any(not i["known_booking_platform"] for i in p.get("blind_spots", {}).get("iframes", []))
    ]
    js_button_pages = []
    for p in ev["pages"]:
        btns = p.get("blind_spots", {}).get("js_only_buttons", [])
        clicked_text = {c["button_text"] for c in p.get("cta_clicks", [])}
        remaining = [b for b in btns if b not in clicked_text]
        if remaining:
            js_button_pages.append((p, remaining))
    if other_iframe_pages or js_button_pages:
        L.append("\n## ⚠️ OTHER UNVERIFIED INTERACTIVE ELEMENTS")
        L.append("Static crawl + screenshot can't fully verify these — read the raw page "
                 "text/HTML or open the live page by hand before calling anything here a finding.")
        for p in other_iframe_pages:
            srcs = [i["src"] for i in p["blind_spots"]["iframes"] if not i["known_booking_platform"]]
            L.append(f"- {p['url']} — unrecognized iframe(s): {', '.join(srcs[:3])}")
        for p, remaining in js_button_pages:
            L.append(f"- {p['url']} — {len(remaining)} JS-only button(s), destination not verified: "
                     + ", ".join(f'"{b}"' for b in remaining[:5]))

    # Floors
    L.append("\n## Floor signals (Gate 0)")
    for f in ev["floors"]["floors"]:
        mark = {"pass": "✅", "fail": "❌", "needs_review": "❓"}[f["verdict"]]
        L.append(f"- {mark} **{f['floor']}** — {f['evidence']}")
    if ev["floors"]["hard_fail"]:
        L.append("\n**HARD FAIL on the floor → Lane 3 unless an equivalent signal overrides.**")

    # The 5-stop walk — every stop reports a result, never blank.
    L.append("\n## 5-Stop Walk")
    _STOP_LABEL = {"bio": "Stop 1 — Bio", "freebie": "Stop 2 — Freebie",
                   "offer": "Stop 3 — Offer/Sales", "checkout": "Stop 4 — Checkout",
                   "audience": "Stop 5 — Audience Ownership"}
    _STATUS_MARK = {"found": "✅ FOUND", "not_found": "⭕ NOT FOUND",
                    "not_reached": "⭕ NOT REACHED", "blocked": "🚫 BLOCKED"}
    for s in ev["walk_stops"]:
        L.append(f"- **{_STOP_LABEL[s['stop']]}** — {_STATUS_MARK[s['status']]} — {s['detail']}")

    # Reconciliation — the primary output. Cross-page mismatches lead over
    # anything found by reading a single page in isolation.
    L.append("\n## Reconciliation (cross-page diff — read this before anything else below)")
    if not ev["reconciliation"]:
        L.append("- No cross-page mismatches found (dates, prices, or curriculum counts all "
                 "consistent between offer and checkout pages, where both were reached).")
    else:
        for r in sorted(ev["reconciliation"], key=lambda x: x["tier"]):
            L.append(f"- **[Tier {r['tier']} — {r['kind']}]** {r['summary']} — {r['where']}")
            if r.get("note"):
                L.append(f"  - {r['note']}")

    # Emails
    L.append("\n## Harvested contact emails")
    he = ev["harvested_emails"]
    if not he["personal"] and not he["generic"]:
        L.append("- None visible from the crawl. Next steps per Email OS: freebie opt-in reply-to, "
                 "podcast/YouTube notes, Google search, pattern guess + verify.")
    for e in he["personal"]:
        tag = "matches lead name" if e.get("name_match") else "personal-looking"
        L.append(f"- **{e['email']}** ({tag}) — found on {e['source']}")
    for e in he["generic"]:
        L.append(f"- {e['email']} (generic) — found on {e['source']}")

    # Leak candidates — single-page observations, secondary to reconciliation above.
    L.append("\n## Machine-flagged leak candidates (single-page — see Reconciliation above first)")
    if not ev["leak_candidates"]:
        L.append("- None auto-detected. That does NOT mean Lane 2 — read the pages; "
                 "copy/offer/sequencing leaks don't auto-detect.")
    for c in ev["leak_candidates"]:
        L.append(f"- **[Stop {c['stop']} / Tier {c['tier']} candidate]** {c['what']} — {c['where']}")
        if c["note"]:
            L.append(f"  - {c['note']}")

    # External references — visible but explicitly out of scope
    if ev.get("external_refs"):
        L.append("\n## External references (NOT crawled — not her funnel)")
        L.append("Press mentions, directories, designer credits, and other third-party "
                 "sites linked from her pages. Nothing on these domains is her leak.")
        for r in ev["external_refs"][:12]:
            label = f" ({r['label']})" if r.get("label") else ""
            L.append(f"- {r['url']}{label}")

    # Pages
    L.append("\n## Page-by-page")
    for i, p in enumerate(ev["pages"], start=1):
        ext = " — EXTERNAL (platform page, not her site)" if p.get("external") else ""
        L.append(f"\n### [{i}] {p['link_type'].upper()} — {p['url']}{ext}")
        if p["error"]:
            L.append(f"**FAILED TO LOAD:** {p['error'][:260]}")
            continue
        if p["title"]:
            L.append(f"Title: {p['title']}")
        ck = p["checks"]
        speed = ck.get("speed", {})
        forms = ck.get("forms", {})
        pix = ck.get("pixels", {})
        links = ck.get("links", {})
        co = ck.get("checkout", {})
        summary = [
            f"load {speed.get('load_ms', 0)}ms ({speed.get('verdict', '?')})",
            f"email form: {'yes' + (' (' + forms['platform_detected'] + ')' if forms.get('platform_detected') else '') if forms.get('form_present') else 'no'}",
            f"pixels: {'yes' if pix.get('any_present') else 'none'}",
            f"broken links: {len(links.get('broken', []))}",
        ]
        if co.get("platform") and (co.get("transacts") or p["link_type"] == "checkout"):
            summary.append(f"checkout platform: {co['platform']}")
            summary.append(f"order bump: {'yes' if co.get('order_bump_detected') else 'no'}")
        L.append("Checks: " + " • ".join(summary))
        if p["headings"]:
            L.append("Headings: " + " | ".join(p["headings"][:8]))
        if p["prices"]:
            L.append("Prices seen: " + "; ".join(
                f"{x['price']} (“…{x['context'][:70]}…”)" for x in p["prices"][:5]
            ))
        for a in p.get("availability", [])[:5]:
            L.append(f"AVAILABILITY: [{a['kind']}] \"{a['match']}\" — context: …{a['context'][:120]}…")
        stale = [d for d in p["dates"] if d["stale_candidate"]]
        if stale:
            for d in stale[:3]:
                L.append(f"STALE DATE CANDIDATE: \"{d['raw']}\" parsed {d['parsed']} "
                         f"({d['days_past']} days past{', year assumed' if d['year_assumed'] else ''}) — "
                         f"context: …{d['context'][:120]}…")
        if p.get("text_inline"):
            L.append("Key copy (first %d chars):" % len(p["text_inline"]))
            L.append("```")
            L.append(p["text_inline"].strip())
            L.append("```")
        if p["screenshot_desktop"] or p["screenshot_mobile"]:
            L.append(f"Screenshots: {p['screenshot_desktop']} | {p['screenshot_mobile']}")
        if p.get("booking_embed"):
            L.append(f"⚠️ Contains an inline `{p['booking_embed']}` booking widget — "
                     "screenshot may show this as blank space even when it's live and working. "
                     "Do not call a nearby gap a missing CTA without verifying against the raw "
                     "page text or the live page.")
        if p["text_file"]:
            L.append(f"Full text: {p['text_file']}")

    # Blind spots
    L.append("\n## Not visible from this crawl (fill by hand / Claude search)")
    L.append("- IG activity + engagement (activity floor) — verify via web search")
    L.append("- Comment-for-freebie and DM-gated flows; manual vs automated delivery")
    L.append("- Anything behind a login or a real payment attempt")
    L.append("- Email delivery + follow-up sequence (ghost test: opt in, wait 48h)")
    L.append("- Tone, friction, and how the pages *feel* to click through")
    L.append("")
    return "\n".join(L)
