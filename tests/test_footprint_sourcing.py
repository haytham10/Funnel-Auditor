"""Tests for the Google-footprint sourcing helpers added 2026-07-16
(audit/apify.py):

  1. _host_of — bare host for per-site dedup (achievher.com/ and
     achievher.com/login collapse; distinct *.mykajabi.com subdomains do not).
  2. _is_footprint_noise — the footer-signature net drags in the platform's
     own site and social posts; those are dropped, a coach's real
     *.mykajabi.com funnel and their custom domain are kept.
  3. PLATFORM_FOOTPRINTS — every platform carries a domain; only the
     community-first one (skool) has no funnel footer marker.

Run: python -m pytest tests/test_footprint_sourcing.py -q
     (or plain `python tests/test_footprint_sourcing.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import apify


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
