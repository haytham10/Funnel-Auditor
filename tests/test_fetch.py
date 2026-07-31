"""Tier 0 — the free local site read, and what it hands the stages after it.

This file exists because the first real batch crashed here on the first page of
the first site. `extract_emails` returns a dict of two buckets, `_harvest` did
`read.emails.extend(...)` on it, and `list.extend(dict)` iterates the KEYS — so
`read.emails` filled up with the strings "personal" and "generic" and then blew
up on `.get`. Nothing caught it because nothing had ever run tier 0 against a
real page: the crash is unreachable with an empty page list, which is what every
other test had.

So the rule here is that every test feeds real HTML through the real harvest.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import fetch


PAGE = """
<html><body>
  <h1>Coaching for founders</h1>
  <h2>Programmes</h2>
  <p>Reach me at <a href="mailto:sarah@coachsite.ae">sarah@coachsite.ae</a>
     or the office on info@coachsite.ae.</p>
  <p>Packages from AED 12,000.</p>
  <a href="https://linkedin.com/in/sarahcoach">LinkedIn</a>
  <a href="https://instagram.com/sarahcoach">Instagram</a>
</body></html>
"""


def read_of(*pages) -> fetch.SiteRead:
    """A SiteRead carrying real pages, then harvested exactly as tier 0 does."""
    read = fetch.SiteRead(domain="coachsite.ae")
    for url, html in pages:
        read.pages.append(fetch.Page(url=url, status=200, html=html,
                                     text=fetch.visible_text(html)))
    fetch._harvest(read, "https://coachsite.ae")
    return read


def test_harvest_returns_email_dicts_not_bucket_names():
    """The crash. `extend` on a dict iterates its keys."""
    read = read_of(("https://coachsite.ae", PAGE))
    assert read.emails, "nothing harvested"
    for entry in read.emails:
        assert isinstance(entry, dict), entry
        assert entry.get("email"), entry
    addresses = [e["email"] for e in read.emails]
    assert "personal" not in addresses and "generic" not in addresses


def test_a_personal_address_outranks_a_generic_one():
    read = read_of(("https://coachsite.ae", PAGE))
    addresses = [e["email"] for e in read.emails]
    assert addresses.index("sarah@coachsite.ae") < addresses.index("info@coachsite.ae")


def test_a_personal_address_on_a_later_page_still_outranks_an_early_generic():
    """Ranking by page order would hand the batch a mailbox nobody reads. The
    buckets stay apart until the end for exactly this."""
    generic_first = '<html><body><a href="mailto:info@coachsite.ae">c</a></body></html>'
    personal_later = '<html><body><a href="mailto:sarah@coachsite.ae">s</a></body></html>'
    read = read_of(("https://coachsite.ae", generic_first),
                   ("https://coachsite.ae/about", personal_later))
    assert read.emails[0]["email"] == "sarah@coachsite.ae"


def test_the_same_address_on_two_pages_appears_once():
    read = read_of(("https://coachsite.ae", PAGE),
                   ("https://coachsite.ae/about", PAGE))
    addresses = [e["email"] for e in read.emails]
    assert len(addresses) == len(set(addresses))


def test_headings_prices_and_socials_come_through():
    read = read_of(("https://coachsite.ae", PAGE))
    assert "Coaching for founders" in read.headings
    assert any("12,000" in p["price"] for p in read.prices)
    assert read.social.get("linkedin", "").endswith("/in/sarahcoach")
    assert "instagram" in read.social


def test_a_page_with_no_html_is_skipped_not_fatal():
    read = fetch.SiteRead(domain="coachsite.ae")
    read.pages.append(fetch.Page(url="https://coachsite.ae", status=500,
                                 html="", text=""))
    fetch._harvest(read, "https://coachsite.ae")
    assert read.emails == [] and read.headings == []


def test_an_empty_read_harvests_to_nothing():
    read = read_of()
    assert read.emails == [] and read.headings == [] and read.social == {}


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
