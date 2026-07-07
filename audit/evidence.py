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

from audit.crawler import CrawlResult, CrawledPage
from audit.checks import (
    check_pixels, check_forms, check_links, check_meta, check_speed, check_checkout,
)
from audit.extract import (
    visible_text, extract_headings, extract_prices, extract_emails,
    extract_dates, extract_availability, detect_foreign_currency,
)
from audit.gates import evaluate_floors
from audit.urls import same_site

TEXT_INLINE_CHARS = 700       # how much page text goes inline in packet.md
TEXT_FILE_MAX_CHARS = 20000   # cap per page text file

_OFFER_PAGE_TYPES = ("sales", "course", "checkout", "booking", "freebie", "opt-in")


@dataclass
class PageEvidence:
    page: CrawledPage
    checks: dict = field(default_factory=dict)
    headings: list = field(default_factory=list)
    prices: list = field(default_factory=list)
    emails: dict = field(default_factory=dict)
    dates: list = field(default_factory=list)
    availability: list = field(default_factory=list)
    foreign_currency: str | None = None
    text: str = ""
    text_file: str = ""


def _slug(value: str) -> str:
    value = re.sub(r"^https?://(www\.)?", "", value.strip().lower())
    value = re.sub(r"[^\w]+", "-", value).strip("-")
    return value[:60] or "lead"


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
    if page.foreign_locale_html:
        ev.foreign_currency = detect_foreign_currency(
            ev.text, visible_text(page.foreign_locale_html)
        )
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
                if p.foreign_currency:
                    add(4, "B",
                        f"Checkout defaults non-US visitors into {p.foreign_currency} "
                        "with no easy way back to USD", pg.url,
                        "Verified by re-fetching this checkout as a non-US visitor (locale/timezone "
                        "probe) — the price this page shows depends on where the visitor is browsing "
                        "from, invisible to a normal US-locale crawl. Every non-US sale on this link "
                        "starts with a currency-confusion moment before checkout.")
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
                "text_inline": p.text[:TEXT_INLINE_CHARS],
                "headings": p.headings,
                "prices": p.prices,
                "emails": p.emails,
                "dates": p.dates,
                "availability": p.availability,
                "checks": p.checks,
            }
            for p in pages
        ],
    }
    (out / "evidence.json").write_text(json.dumps(evidence, indent=2, default=str))
    (out / "packet.md").write_text(_render_packet(evidence))
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

    # Floors
    L.append("\n## Floor signals (Gate 0)")
    for f in ev["floors"]["floors"]:
        mark = {"pass": "✅", "fail": "❌", "needs_review": "❓"}[f["verdict"]]
        L.append(f"- {mark} **{f['floor']}** — {f['evidence']}")
    if ev["floors"]["hard_fail"]:
        L.append("\n**HARD FAIL on the floor → Lane 3 unless an equivalent signal overrides.**")

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

    # Leak candidates
    L.append("\n## Machine-flagged leak candidates")
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
            L.append("Key copy (first %d chars):" % TEXT_INLINE_CHARS)
            L.append("```")
            L.append(p["text_inline"].strip())
            L.append("```")
        if p["screenshot_desktop"] or p["screenshot_mobile"]:
            L.append(f"Screenshots: {p['screenshot_desktop']} | {p['screenshot_mobile']}")
        if p["text_file"]:
            L.append(f"Full text: {p['text_file']}")

    # Blind spots
    L.append("\n## Not visible from this crawl (fill by hand / Claude search)")
    L.append("- IG activity + engagement (activity floor) — verify via web search")
    L.append("- Comment-for-freebie and DM-gated flows; manual vs automated delivery")
    L.append("- Anything behind a login or a real payment attempt")
    L.append("- Email delivery + follow-up sequence (ghost test: opt in, wait 48h)")
    L.append("- Tone, friction, and how the pages *feel* to click through")
    L.append("- IP-geolocation-based currency defaulting on checkout pages (a locale/timezone "
             "probe runs automatically and catches SOME cases, but platforms that key off the "
             "visitor's real IP — not browser locale — need a human check: VPN from abroad, or "
             "ask a contact in another country to screenshot the checkout)")
    L.append("")
    return "\n".join(L)
