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

import threading

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


# ---------------------------------------------------------- the escalation plan


def test_the_plan_names_a_vetted_actor_key():
    """It used to name `apify/website-content-crawler` in the slash form, which
    was in no ACTORS map — so nothing could run it through the cost gate, it
    was something the operator executed by hand outside the approval path, and
    the first real batch skipped the whole stage."""
    from audit import apify

    plan = fetch.apify_batch_plan(["https://a.ae"], render=False)
    assert plan["actor_key"] in apify.ACTORS
    assert fetch.apify_batch_plan(["https://a.ae"], render=True)["actor_key"] \
        in apify.ACTORS


def test_the_static_and_render_paths_are_different_actors():
    assert (fetch.apify_batch_plan(["https://a.ae"], render=False)["actor_key"]
            != fetch.apify_batch_plan(["https://a.ae"], render=True)["actor_key"])


def test_the_plan_dedupes_and_keeps_one_run():
    plan = fetch.apify_batch_plan(["https://a.ae", "https://b.ae", "https://a.ae"])
    assert plan["urls"] == ["https://a.ae", "https://b.ae"]


def test_run_plan_dispatches_to_the_right_crawler(monkeypatch):
    from audit import apify

    calls = []
    monkeypatch.setattr(apify, "crawl_static",
                        lambda urls, **k: calls.append(("static", urls)) or [])
    monkeypatch.setattr(apify, "crawl_render",
                        lambda urls, **k: calls.append(("render", urls)) or [])
    fetch.run_plan(fetch.apify_batch_plan(["https://a.ae"], render=False))
    fetch.run_plan(fetch.apify_batch_plan(["https://b.ae"], render=True))
    assert [c[0] for c in calls] == ["static", "render"]


# ------------------------------------------------------------- concurrency


class _Lead:
    def __init__(self, i):
        self.site_url = f"https://site{i}.ae"
        self.email = f"a{i}@x.ae"
        self.slug = f"lead{i}"


def test_batch_fetch_reads_every_lead_exactly_once(monkeypatch):
    """Concurrency must not drop or duplicate a lead. Results go into a dict
    keyed by `_read_key`, so completion order cannot leak into the output."""
    seen = []
    lock = threading.Lock()

    def fake_read(url, **kwargs):
        with lock:
            seen.append(url)
        read = fetch.SiteRead(domain=url)
        read.pages = [fetch.Page(url=url, status=200, text="x" * 500)]
        return read
    monkeypatch.setattr(fetch, "read_site", fake_read)

    leads = [_Lead(i) for i in range(20)]
    out = fetch.batch_fetch(leads, workers=8)
    assert len(out["reads"]) == 20
    assert sorted(seen) == sorted(l.site_url for l in leads)
    assert out["ok"] == 20
    assert out["workers"] == 8


def test_each_worker_gets_its_own_session(monkeypatch):
    """`requests.Session` is not thread-safe — its connection pool and cookie
    jar are shared mutable state — so the single shared session the serial loop
    used could not simply be handed to a pool."""
    sessions = set()
    lock = threading.Lock()

    def fake_read(url, *, max_pages=5, session=None, **kwargs):
        with lock:
            sessions.add(id(session))
        return fetch.SiteRead(domain=url)
    monkeypatch.setattr(fetch, "read_site", fake_read)
    fetch.batch_fetch([_Lead(i) for i in range(12)], workers=4)
    assert len(sessions) <= 4 and None not in sessions


def test_a_single_worker_still_works(monkeypatch):
    """`--workers 1` restores the serial loop, which is the fallback if
    concurrency ever turns out to trip a host."""
    monkeypatch.setattr(fetch, "read_site",
                        lambda url, **k: fetch.SiteRead(domain=url))
    out = fetch.batch_fetch([_Lead(i) for i in range(3)], workers=1)
    assert len(out["reads"]) == 3 and out["workers"] == 1


def test_an_empty_batch_does_not_divide_by_zero(monkeypatch):
    out = fetch.batch_fetch([], workers=8)
    assert out["attempted"] == 0 and out["tier0_rate"] == 0.0
