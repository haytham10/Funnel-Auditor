"""Tests for audit/urls.py host handling — in particular the www-strip that
used to be `lstrip("www.")`, a character-set strip that mangled any host
starting with a run of w/. characters (wine.com -> ine.com).

Run: python -m pytest tests/test_urls.py -q
     (or plain `python tests/test_urls.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit.urls import strip_www, registrable_domain, normalize


# --- strip_www -------------------------------------------------------------

def test_strip_www_removes_leading_www_label():
    assert strip_www("www.site.com") == "site.com"


def test_strip_www_leaves_bare_host_untouched():
    assert strip_www("site.com") == "site.com"


def test_strip_www_does_not_eat_leading_w_chars():
    # The bug: lstrip("www.") turned wine.com into ine.com.
    assert strip_www("wine.com") == "wine.com"
    assert strip_www("web.site.com") == "web.site.com"
    # only the literal "www." prefix is stripped — no "." after www, no strip
    assert strip_www("wwworld.com") == "wwworld.com"


# --- registrable_domain: regression + preserved behavior -------------------

def test_registrable_domain_w_starting_host_not_mangled():
    # Was 'ine.com' under the old lstrip bug.
    assert registrable_domain("https://wine.com") == "wine.com"
    assert registrable_domain("wine.com") == "wine.com"


def test_registrable_domain_strips_real_www():
    assert registrable_domain("www.wine.com") == "wine.com"
    assert registrable_domain("https://www.example.com/path") == "example.com"


def test_registrable_domain_two_level_suffix_preserved():
    assert registrable_domain("shop.example.co.uk") == "example.co.uk"
    assert registrable_domain("https://courses.coach-site.com") == "coach-site.com"


def test_registrable_domain_bare_two_label():
    assert registrable_domain("example.com") == "example.com"


# --- normalize still folds www consistently --------------------------------

def test_normalize_strips_www_and_keeps_w_hosts():
    assert normalize("https://www.site.com/") == "https://site.com"
    assert normalize("https://wine.com/") == "https://wine.com"


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
