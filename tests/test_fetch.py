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

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Standalone runs get no conftest, and batch_fetch writes a ledger line per page.
os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

import threading

import pytest

from outbound import fetch, ledger


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


# --------------------------------------------- what is NOT somebody's profile

# A tracking pixel and an embedded post sit in the <head>; the social bar sits
# in the footer. `_harvest` takes the leftmost match, so the infrastructure won.
TRACKED_PAGE = """
<html><head>
  <script>fbq('init', '123');</script>
  <img height="1" width="1" src="https://www.facebook.com/tr?id=123&ev=PageView"/>
  <iframe src="https://www.facebook.com/plugins/page.php?href=x"></iframe>
  <blockquote class="instagram-media"
     data-instgrm-permalink="https://www.instagram.com/p/CxYz123/"></blockquote>
</head><body>
  <a href="https://www.facebook.com/sharer.php?u=https://coachsite.ae">Share</a>
  <footer>
    <a href="https://www.facebook.com/sarahkhancoach">Facebook</a>
    <a href="https://www.instagram.com/sarahkhancoach/">Instagram</a>
  </footer>
</body></html>
"""


def test_the_meta_pixel_is_not_harvested_as_their_facebook_page():
    """`facebook.com/tr` is the Meta pixel. It was winning on every lead running
    ads, and once ownership is typed it scores `absent` and reads as a name
    collision rather than as a tracking script."""
    read = read_of(("https://coachsite.ae", TRACKED_PAGE))
    assert read.social.get("facebook") == "https://facebook.com/sarahkhancoach"


def test_an_embedded_post_is_not_harvested_as_their_instagram_profile():
    """`instagram.com/p/<id>` is one post, embedded — usually somebody else's."""
    read = read_of(("https://coachsite.ae", TRACKED_PAGE))
    assert read.social.get("instagram") == "https://instagram.com/sarahkhancoach"


def test_a_podcast_and_an_x_handle_are_harvested():
    """Rung 2 of the hook ladder — the one that reaches the coaches who do not
    post — had no host pattern at all, so it was served entirely by an agent
    improvising a web search, which is the most expensive way to find a URL."""
    page = ('<html><body>'
            '<a href="https://twitter.com/intent/tweet?text=hi">Tweet this</a>'
            '<a href="https://open.spotify.com/show/4abcXYZ">The podcast</a>'
            '<a href="https://x.com/sarahkhancoach">X</a>'
            '</body></html>')
    read = read_of(("https://coachsite.ae", page))
    assert read.social.get("podcast") == "https://open.spotify.com/show/4abcXYZ"
    assert read.social.get("twitter") == "https://x.com/sarahkhancoach"


def test_a_share_link_is_not_harvested_as_a_profile():
    """A share button names the page being shared, not a page anybody owns."""
    only_share = ('<html><body><a href="https://www.facebook.com/sharer.php'
                  '?u=https://coachsite.ae">Share</a></body></html>')
    read = read_of(("https://coachsite.ae", only_share))
    assert "facebook" not in read.social


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


def test_run_plan_refuses_a_non_site_actor_and_spends_nothing(monkeypatch):
    """A `li_profile` batch must not quietly become a cheerio run.

    This used to fall through to `crawl_static`, which would have paid to run a
    static HTML scraper against LinkedIn URLs and returned empty items that look
    like a lead with nothing on their profile.
    """
    from audit import apify

    calls = []
    monkeypatch.setattr(apify, "crawl_static",
                        lambda urls, **k: calls.append(("static", urls)) or [])
    monkeypatch.setattr(apify, "crawl_render",
                        lambda urls, **k: calls.append(("render", urls)) or [])

    for key in ("li_profile", "li_posts", "", None):
        with pytest.raises(ValueError) as exc:
            fetch.run_plan({"actor_key": key,
                            "urls": ["https://linkedin.com/in/someone"]})
        assert repr(key) in str(exc.value)
    assert calls == []


# ------------------------------------------------------------- concurrency


class _Lead:
    def __init__(self, i):
        self.site_url = f"https://site{i}.ae"
        self.email = f"a{i}@x.ae"
        self.slug = f"lead{i}"


def test_batch_fetch_reads_every_lead_exactly_once(monkeypatch):
    """Concurrency must not drop or duplicate a lead. Results go into a dict
    keyed by `lead_key`, so completion order cannot leak into the output."""
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


# ------------------------------------------------ the leads tier 0 cannot help


class _Social:
    def __init__(self, name, site="", instagram="", linkedin=""):
        self.name, self.site_url = name, site
        self.instagram_url, self.linkedin_url = instagram, linkedin
        self.facebook_url = self.youtube_url = ""
        self.email = f"{name.lower()}@x.ae"
        self.slug = name.lower()
        self.company = self.city = ""

    def social_urls(self):
        return [u for u in (self.linkedin_url, self.instagram_url,
                            self.facebook_url, self.youtube_url) if u]


def test_a_lead_with_no_site_and_no_social_is_named_for_search():
    """It produced nothing at all before, so each research worker met it cold
    and improvised — which is how the last batch used WebSearch without it
    being a rung anybody had planned."""
    out = fetch.batch_fetch([_Social("Nobody")], workers=2)
    assert [l["name"] for l in out["needs_search"]] == ["Nobody"]
    assert out["ig_only"] == []


def test_a_lead_reachable_only_on_instagram_is_named_for_ig():
    out = fetch.batch_fetch(
        [_Social("Iggy", instagram="https://instagram.com/iggy")], workers=2)
    assert [l["url"] for l in out["ig_only"]] == ["https://instagram.com/iggy"]
    assert out["needs_search"] == []


def test_a_lead_with_another_social_is_not_ig_only():
    out = fetch.batch_fetch([_Social("Both",
                                     instagram="https://instagram.com/b",
                                     linkedin="https://linkedin.com/in/b")],
                            workers=2)
    assert out["ig_only"] == [] and out["needs_search"] == []


def test_a_lead_with_a_site_is_neither(monkeypatch):
    monkeypatch.setattr(fetch, "read_site",
                        lambda url, **k: fetch.SiteRead(domain=url))
    out = fetch.batch_fetch([_Social("Sited", site="https://a.ae")], workers=2)
    assert out["ig_only"] == [] and out["needs_search"] == []


# ------------------------------------------------------- does the site say them


def _read_with(text, name_in_page=True, ok=True):
    read = fetch.SiteRead(domain="x.ae")
    body = ("Sarah Khan is a leadership coach in Dubai." if name_in_page
            else "A retreat house in Ohio. Come and stay.")
    read.pages = [fetch.Page(url="https://x.ae", status=200 if ok else 404,
                             text=(body + " " + text) * 20)]
    return read


def test_a_site_that_names_the_lead_is_confirmed():
    assert fetch.check_owner(_read_with(""), "Sarah Khan") == "confirmed"


def test_a_site_that_never_names_the_lead_is_absent():
    """About 40 of 151 rows pointed at somebody else — parked domains, name
    collisions, a coach's training school, an Ohio retreat house. Nothing
    checked, so every one was found by hand after the fetch was paid for."""
    assert fetch.check_owner(_read_with("", name_in_page=False),
                             "Sarah Khan") == "absent"


def test_an_unreadable_site_is_unknown_not_absent():
    """Absence of evidence. A site that would not load says nothing about who
    owns it, and reporting that as a mismatch would be a lie."""
    assert fetch.check_owner(_read_with("", ok=False), "Sarah Khan") == "unknown"


def test_no_name_to_check_is_unknown():
    assert fetch.check_owner(_read_with(""), "") == "unknown"


def test_an_initial_is_too_short_to_confirm_ownership():
    """min_len=3, so "S" cannot match every site on earth."""
    assert fetch.check_owner(_read_with("", name_in_page=False), "S K") == "unknown"


def test_the_owner_check_is_reported_and_never_a_kill(monkeypatch):
    monkeypatch.setattr(fetch, "read_site",
                        lambda url, **k: _read_with("", name_in_page=False))
    out = fetch.batch_fetch([_Social("Nobody Here", site="https://x.ae")], workers=2)
    assert [u["name"] for u in out["unowned"]] == ["Nobody Here"]
    assert "OWNER-CHECK" in out["report"]
    # Still read, still counted, still available to every later stage.
    assert out["attempted"] == 1


# --------------------------------------------------------------- the ledger
#
# `batch_fetch` computed an `elapsed_secs` for the whole batch, printed it, and
# dropped it — the only clock in the entire repo. Nothing knew what any single
# page cost in time, so "tier 0 is free" was true in dollars and unmeasured in
# the thing that actually ran out: wall-clock.


def test_every_page_read_free_lands_in_the_ledger(monkeypatch, tmp_path):
    monkeypatch.setenv("OUTBOUND_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(fetch, "read_site",
                        lambda url, **k: read_of(("https://coachsite.ae", PAGE),
                                                 ("https://coachsite.ae/about", PAGE)))
    fetch.batch_fetch([_Social("Sarah Khan", site="https://coachsite.ae")], workers=2)

    records, _ = ledger.read(None, tmp_path)
    assert len(records) == 2, "one line per page, not one per site"
    assert {r.url for r in records} == {"https://coachsite.ae",
                                        "https://coachsite.ae/about"}
    assert all(r.retrieved_by == "tier0" for r in records)
    assert all(r.cost_usd == 0.0 for r in records)
    assert all(r.stage == "fetch" and r.purpose == "observe" for r in records)


def test_the_ledger_line_is_keyed_to_the_lead_not_the_site(monkeypatch, tmp_path):
    """Two rows from a directory can share a company site. Keying on the site
    would merge their spend, which is the same bug `lead_key` exists for."""
    monkeypatch.setenv("OUTBOUND_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(fetch, "read_site",
                        lambda url, **k: read_of(("https://shared.ae", PAGE)))
    fetch.batch_fetch([_Social("One", site="https://shared.ae"),
                       _Social("Two", site="https://shared.ae")], workers=2)

    records, _ = ledger.read(None, tmp_path)
    assert len({r.lead_key for r in records}) == 2


def test_a_page_that_could_not_be_read_is_recorded_as_an_error(monkeypatch, tmp_path):
    """A site that ate fifteen seconds of timeout and returned nothing is the
    most expensive free page in a batch. Recording only the good ones hides it."""
    monkeypatch.setenv("OUTBOUND_LEDGER_ROOT", str(tmp_path))

    def dead(url, **k):
        read = fetch.SiteRead(domain="dead.ae")
        read.pages.append(fetch.Page(url="https://dead.ae", error="ConnectTimeout",
                                     secs=15.0))
        return read
    monkeypatch.setattr(fetch, "read_site", dead)
    fetch.batch_fetch([_Social("Gone", site="https://dead.ae")], workers=2)

    records, _ = ledger.read(None, tmp_path)
    assert records[0].outcome == "error"
    assert records[0].secs == 15.0


def test_a_page_that_returned_nothing_is_empty_not_ok():
    """200 with no text is the JS-render signature, and the only honest reason
    to pay for a browser. It must not read as a successful free fetch."""
    thin = fetch.Page(url="https://x.ae", status=200, html="<html></html>", text="")
    assert thin.thin and thin.outcome == "empty"


def test_get_page_times_itself(monkeypatch):
    """The first per-retrieval clock in the repo."""
    monkeypatch.setattr(fetch, "visible_text", lambda html: "x" * 500)

    class _Resp:
        status_code = 200
        headers = {"content-type": "text/html"}
        text = "<html><body>hi</body></html>"

    class _Session:
        def get(self, *a, **k):
            return _Resp()

    page = fetch.get_page("https://x.ae", _Session())
    assert page.ok and page.secs >= 0.0 and isinstance(page.secs, float)


# --------------------------------------------------------- the standalone path

# This block used to sit at line 108 of a 396-line file, so `python
# tests/test_fetch.py` defined and ran the first seven tests and exited — every
# `check_owner`, ledger and escalation-plan test below it was never even
# reached, and the run printed "0 failure(s)". It has to be last.
#
# Eleven of these tests take a pytest fixture (`monkeypatch`, `tmp_path`), which
# this runner cannot supply. It names them as SKIP rather than calling them and
# reporting the TypeError as a failure: a runner that lies about coverage is the
# thing being fixed here, and one that cries wolf is the next version of it.

if __name__ == "__main__":
    import inspect

    failures, skipped = 0, 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        if inspect.signature(fn).parameters:
            skipped += 1
            print(f"SKIP {name} (needs a pytest fixture)")
            continue
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s), {skipped} skipped — "
          f"run under pytest for the fixture-taking ones")
    sys.exit(1 if failures else 0)
