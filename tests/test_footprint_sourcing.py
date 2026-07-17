"""Tests for the Google-footprint sourcing helpers added 2026-07-16
(audit/apify.py), moved to the fetch-agnostic audit/footprint.py 2026-07-17:

  1. _host_of — bare host for per-site dedup (achievher.com/ and
     achievher.com/login collapse; distinct *.mykajabi.com subdomains do not).
  2. _is_footprint_noise — the footer-signature net drags in the platform's
     own site and social posts; those are dropped, a coach's real
     *.mykajabi.com funnel and their custom domain are kept.
  3. PLATFORM_FOOTPRINTS — every platform carries a domain; only the
     community-first one (skool) has no funnel footer marker.
  4. classify_footprint_hits — the fetch-agnostic merge (audit/footprint.py),
     fed pre-fetched hits directly (as Firecrawl search would supply) rather
     than through apify.google_search.

apify._host_of / apify._is_footprint_noise / apify.PLATFORM_FOOTPRINTS are
re-exports of audit.footprint's originals, kept for backward compatibility.

Run: python -m pytest tests/test_footprint_sourcing.py -q
     (or plain `python tests/test_footprint_sourcing.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import apify, footprint


# --- _host_of --------------------------------------------------------------

def test_host_strips_scheme_path_and_www():
    assert apify._host_of("https://www.achievher.com/login") == "achievher.com"
    assert apify._host_of("https://www.achievher.com/") == "achievher.com"


def test_host_keeps_distinct_subdomains_apart():
    a = apify._host_of("https://shelley-bosworth-coaching.mykajabi.com/x")
    b = apify._host_of("https://kirsty-mcintyre.mykajabi.com/")
    assert a != b  # two different free-tier coaches must not collapse


def test_same_site_two_paths_collapse():
    a = apify._host_of("https://www.achievher.com/login")
    b = apify._host_of("http://achievher.com/about")
    assert a == b  # one coach, one candidate


# --- _is_footprint_noise ---------------------------------------------------

def test_platform_own_site_is_noise():
    assert apify._is_footprint_noise("https://kajabi.com/")
    assert apify._is_footprint_noise("https://www.teachable.com/pricing")


def test_social_hosts_are_noise():
    assert apify._is_footprint_noise("https://www.instagram.com/p/DUWYOkqEuf-/")
    assert apify._is_footprint_noise("https://www.facebook.com/groups/x/posts/1/")


def test_real_custom_domain_is_not_noise():
    assert not apify._is_footprint_noise("https://www.achievher.com/")


def test_coach_subdomain_is_not_noise():
    # A coach's own *.mykajabi.com funnel is a real hit, not the platform site.
    assert not apify._is_footprint_noise("https://unboxleadership.mykajabi.com/x")


# --- PLATFORM_FOOTPRINTS ---------------------------------------------------

def test_every_platform_has_a_domain():
    for name, fp in apify.PLATFORM_FOOTPRINTS.items():
        assert fp.get("domain"), name


def test_only_skool_has_no_marker():
    no_marker = [k for k, v in apify.PLATFORM_FOOTPRINTS.items() if not v.get("marker")]
    assert no_marker == ["skool"]


def test_footprint_search_rejects_unknown_platform():
    try:
        apify.footprint_search("wordpress")
    except apify.ApifyError as e:
        assert "unknown platform" in str(e)
    else:
        raise AssertionError("expected ApifyError for unknown platform")


# --- classify_footprint_hits (fetch-agnostic, Firecrawl-fed) ----------------

def test_classify_rejects_unknown_platform():
    try:
        footprint.classify_footprint_hits("wordpress", [], [])
    except footprint.FootprintError as e:
        assert "unknown platform" in str(e)
    else:
        raise AssertionError("expected FootprintError for unknown platform")


def test_classify_merges_and_tags_both_shapes():
    sub_hits = [{"url": "https://kirsty-mcintyre.mykajabi.com/"}]
    marker_hits = [{"url": "https://achievher.com/"}, {"url": "https://kajabi.com/"}]
    out = footprint.classify_footprint_hits("kajabi", sub_hits, marker_hits, geo="Dubai")
    assert out["subdomain_count"] == 1
    assert out["footprint_count"] == 1  # kajabi.com itself is filtered as noise
    hosts = {h["url"] for h in out["hits"]}
    assert "https://kirsty-mcintyre.mykajabi.com/" in hosts
    assert "https://achievher.com/" in hosts
    assert "https://kajabi.com/" not in hosts
    found_via = {h["url"]: h["foundVia"] for h in out["hits"]}
    assert found_via["https://kirsty-mcintyre.mykajabi.com/"] == "subdomain"
    assert found_via["https://achievher.com/"] == "footprint"


def test_classify_dedupes_by_host_across_both_shapes():
    # Same host surfacing via both query shapes counts once, keeping whichever
    # shape's hit is processed first (subdomain is processed before marker).
    sub_hits = [{"url": "https://achievher.com/"}]
    marker_hits = [{"url": "https://achievher.com/about"}]
    out = footprint.classify_footprint_hits("kajabi", sub_hits, marker_hits)
    assert len(out["hits"]) == 1
    assert out["hits"][0]["foundVia"] == "subdomain"


def test_classify_skool_has_no_marker_query():
    out = footprint.classify_footprint_hits("skool", [], [])
    assert len(out["queries"]) == 1
    assert "site:skool.com" in out["queries"][0]


def test_classify_hits_missing_url_are_skipped():
    out = footprint.classify_footprint_hits("kajabi", [{"title": "no url here"}], [])
    assert out["hits"] == []
    assert out["subdomain_count"] == 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
