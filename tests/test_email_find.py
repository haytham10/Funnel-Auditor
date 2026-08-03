"""Published-address retrieval: the citation/claim split and the noise filters.

Every case here is a real shape from the 2026-08-03 probe that justified the
rung, because the failures worth pinning are the ones that already happened:
an AI Overview inventing a plausible role address on a real domain, a directory
page carrying both the lead's address and its own, and an overview stating an
absence that is a decision rather than an empty result.

Nothing here fetches. `email_find` never calls a search API — that is
`apify.google_search` — so these are pure-function tests over dataset shapes.

Run: python -m pytest tests/test_email_find.py -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import email_find


def organic(url, title="", description=""):
    return {"url": url, "title": title, "description": description}


def item(organics=(), ai_text=""):
    out = {"organicResults": list(organics)}
    if ai_text:
        out["aiOverview"] = {"content": ai_text}
    return out


# ----------------------------------------------------------------- the query


def test_build_query_drops_the_name_repeated_in_the_headline():
    """IG headlines are "Name | Positioning | City" and the name is already
    the first term. Repeating it wastes query budget and narrows nothing."""
    q = email_find.build_query("Jen de Mel",
                               "Jen de Mel | Diastasis & Postpartum Strength | Dubai")
    assert q.startswith("Jen de Mel ")
    assert q.count("Jen de Mel") == 1
    assert q.endswith("email address")


def test_build_query_survives_a_bare_name():
    assert email_find.build_query("Akram Afify") == "Akram Afify email address"


# ------------------------------------------------------- citation vs. claim


def test_an_organic_hit_is_found_and_carries_its_url():
    r = email_find.find_addresses("Lana Ave", item([
        organic("https://lanawl.com/", "Health Coach UAE",
                "Tel: +97150-6229327 | Email: lana@lanawl.com")]))
    assert r["verdict"] == "FOUND"
    assert r["candidates"][0]["email"] == "lana@lanawl.com"
    assert r["candidates"][0]["provenance"] == "organic"
    assert r["candidates"][0]["source_url"] == "https://lanawl.com/"
    assert r["candidates"][0]["name_match"] is True


def test_an_ai_overview_address_is_claimed_never_found():
    """The probe's actual fabrication: a real domain, a plausible role local
    part, a real cited page — and the mailbox does not exist. It must never
    reach FOUND, because FOUND is what a caller is allowed to act on."""
    r = email_find.find_addresses("Jeff Maingi", item(
        ai_text="A direct email is not listed. General inquiries can be "
                "directed to support@fitbridge.ae, as noted by FitBridge.ae"))
    assert r["verdict"] == "CLAIMED"
    assert r["candidates"][0]["provenance"] == "ai_overview"
    assert r["candidates"][0]["source_url"] == ""
    assert "never adopt" in r["reason"]


def test_an_organic_hit_outranks_an_ai_overview_claim():
    r = email_find.find_addresses("Jeff Maingi", item(
        [organic("https://fitbridge.ae/", "FitBridge", "Contact info@fitbridge.ae")],
        ai_text="Try support@fitbridge.ae"),
        lead_domains=("fitbridge.ae",))
    assert r["verdict"] == "FOUND"
    assert [c["provenance"] for c in r["candidates"]] == ["organic", "ai_overview"]


# ------------------------------------------------------------ corroboration


@pytest.mark.parametrize("name,url,snippet", [
    # Every one of these was reported FOUND by the first live run.
    ("Akram Afify", "https://www.facebook.com/Zetapharma2010/posts/x",
     "Thanks to the exceptional panel of 18 Egyptian experts hend.magdy@purespot.org"),
    ("Sandra Spencer", "https://spencerlodge.tv/mental-health-in-the-workplace/",
     "Mental health in the workplace. Contact sl@spencerlodge.tv"),
    ("Jeff Maingi", "https://www.instagram.com/reel/DXpBu-fgr7f/",
     "Coaching reel andrea@fitqtllc.org"),
    ("Lana Ave", "https://www.thenationalnews.com/lifestyle/wellbeing/x",
     "UAE mental health hotline appointments@sage-clinics.com"),
])
def test_an_address_on_a_page_that_merely_mentions_them_is_not_theirs(name, url, snippet):
    """A query about somebody returns pages that only mention them. The
    address printed on such a page belongs to somebody else by default, and
    with no other candidate the ranking floats it to the top — so this has to
    be a verdict rule, not a ranking one."""
    r = email_find.find_addresses(name, item([organic(url, "", snippet)]))
    assert r["verdict"] != "FOUND"
    assert r["candidates"] == []
    assert len(r["unrelated"]) == 1
    assert "somebody else" in r["reason"]


def test_a_partial_name_hit_does_not_corroborate():
    """`Spencer` alone matched a page about Spencer Lodge. Corroboration needs
    every name token, which is what separates the two Spencers."""
    r = email_find.find_addresses("Sandra Spencer", item([
        organic("https://spencerlodge.tv/", "Spencer Lodge",
                "Spencer Lodge speaks on wellbeing. sl@spencerlodge.tv")]))
    assert r["candidates"] == []


def test_a_page_about_the_lead_does_not_corroborate_a_collaborators_address():
    """The reel genuinely is about Jeff Maingi and the address is Andrea's.
    A page being about somebody corroborates the page, never an address on it
    — collaborators, sponsors and commenters all leave addresses on a person's
    own page."""
    r = email_find.find_addresses("Jeff Maingi", item([
        organic("https://www.instagram.com/reel/DXpBu-fgr7f/", "",
                "Jeff Maingi coaching reel andrea@fitqtllc.org")]))
    assert r["candidates"] == []
    assert len(r["unrelated"]) == 1


def test_a_page_naming_the_lead_in_full_corroborates_a_role_address():
    """How `info@whiteantlergroup.com` qualified before that domain was known
    to be hers: a LinkedIn company page whose snippet names her outright."""
    r = email_find.find_addresses("Sandra Spencer", item([
        organic("https://uk.linkedin.com/company/white-antler-group-llc",
                "White Antler Group LLC",
                "Click here to view Sandra Spencer's profile. For enquiries "
                "contact: info@whiteantlergroup.com")]))
    assert r["verdict"] == "FOUND"
    assert r["candidates"][0]["source_names_lead"] is True


# ------------------------------------------------------------ the absence


def test_a_stated_absence_is_its_own_verdict_and_quotes_the_overview():
    r = email_find.find_addresses("Akram Afify", item(
        ai_text="An official public email address is not listed for Akram "
                "Afify's Soul Therapy Dubai. Bookings are handled directly "
                "through direct messaging."))
    assert r["verdict"] == "ABSENT"
    assert "not listed" in r["absence_note"]
    assert r["candidates"] == []


def test_absence_loses_to_an_address_in_the_serp_underneath():
    """A model hedging in prose while the organic results carry the address is
    the case where trusting the overview would throw a real address away."""
    r = email_find.find_addresses("Lana Ave", item(
        [organic("https://lanawl.com/", "", "Email: lana@lanawl.com")],
        ai_text="A public email address is not listed for this coach."))
    assert r["verdict"] == "FOUND"


def test_nothing_found_and_nothing_said_is_none_not_absent():
    """NONE and ABSENT differ by whether anybody looked, which is the whole
    reason the AI Overview is worth paying for. Collapsing them would make an
    unanswered query look like a confirmed dead end."""
    r = email_find.find_addresses("Jen de Mel", item(
        [organic("https://jendemel.com/", "Jen de Mel", "Book a call")]))
    assert r["verdict"] == "NONE"


def test_a_hedge_is_not_an_absence():
    r = email_find.find_addresses("Someone", item(
        ai_text="Her email may not be easy to find; you might try her website."))
    assert r["verdict"] == "NONE"


# ------------------------------------------------------------ noise filters


def test_the_directory_own_address_is_dropped_and_the_leads_is_kept():
    """One real result from the probe: an accreditation body's instructor page
    carrying both the instructor's address and the body's own contact desk."""
    r = email_find.find_addresses("Jennifer de Mel", item([
        organic("https://oxygenadvantage.com/pages/instructor/jennifer-de-mel",
                "Jennifer de Mel",
                "Email jendemel@icloud.com Website https://www.jendemel.com "
                "teaching and breathing better every day. hello@oxygenadvantage.com")]))
    emails = [c["email"] for c in r["candidates"]]
    assert "jendemel@icloud.com" in emails
    assert "hello@oxygenadvantage.com" not in emails


def test_a_role_address_on_the_leads_own_domain_survives_the_host_filter():
    """`info@whiteantlergroup.com` was found ON a LinkedIn company page, so the
    host differs and the filter must not fire. The filter is about the SOURCE
    site's own desk, never about role accounts as such."""
    r = email_find.find_addresses("Sandra Spencer", item([
        organic("https://uk.linkedin.com/company/white-antler-group-llc",
                "White Antler Group LLC",
                "For enquiries contact: info@whiteantlergroup.com")]),
        lead_domains=("whiteantlergroup.com",))
    assert r["verdict"] == "FOUND"
    assert r["candidates"][0]["email"] == "info@whiteantlergroup.com"
    assert r["candidates"][0]["on_lead_domain"] is True


def test_placeholder_addresses_never_become_candidates():
    """`johnappleseed@gmail.com` was harvested off a real page on the same
    probe and passed the shape gate as `personal`."""
    r = email_find.find_addresses("Lana Ave", item([
        organic("https://whop.com/x", "", "johnappleseed@gmail.com "
                "jane.doe@example.com hello@yourdomain.com")]))
    assert r["candidates"] == []
    assert r["verdict"] == "NONE"


@pytest.mark.parametrize("raw,expected", [
    # The AI Overview runs sentences together with no space after the address.
    ("jendemel@icloud.com.If", "jendemel@icloud.com"),
    # The second shape, live for one run after the first was fixed: the next
    # word glued straight onto the TLD with no separator at all.
    ("jendemel@icloud.comLocation", "jendemel@icloud.com"),
    ("jen@site.comWebsite", "jen@site.com"),
    ("a@b.com.If.Then", "a@b.com"),
    ("A@SITE.COM", "a@site.com"),          # an all-caps TLD must survive
    ("a@b.co.uk", "a@b.co.uk"),
    ("logo@2x.png", ""),
    ("x@y", ""),                            # no dot in the domain at all
])
def test_an_address_is_cut_out_of_running_prose(raw, expected):
    """`.If` read as Iceland's TLD produced a real-looking address that went to
    the verifier and came back a hard bounce."""
    assert email_find._clean(raw) == expected


def test_image_filenames_are_not_addresses():
    r = email_find.find_addresses("X", item([
        organic("https://site.com", "", "logo@2x.png sprite@3x.jpg")]))
    assert r["candidates"] == []


def test_a_name_match_outranks_an_unrelated_organic_hit():
    r = email_find.find_addresses("Jen de Mel", item([
        organic("https://facebook.com/groups/x", "", "misscoexist@gmail.com"),
        organic("https://ukhypopressives.com/project/jen-de-mel/", "",
                "Contact Jen de Mel jendemel@icloud.com")]))
    assert r["candidates"][0]["email"] == "jendemel@icloud.com"


# ------------------------------------------------------------- the exit code


@pytest.mark.parametrize("verdict_item,expected", [
    (item([organic("https://x.com", "", "somebody@z.com")]), 0),        # FOUND
    (item(ai_text="no public email address is listed"), 0),             # ABSENT
    (item(ai_text="reach them at x@y.com"), 1),                         # CLAIMED
    (item([organic("https://x.com", "", "nothing here")]), 1),          # NONE
])
def test_exit_code_treats_a_confirmed_absence_as_an_answer(verdict_item, expected, capsys):
    """ABSENT exits 0 with FOUND. A null result reached honestly has always
    been a good answer in this machine — the hook stage says so too — and an
    exit 1 there would make a correct finding look like a failed command."""
    assert email_find.print_find("Somebody", verdict_item) == expected
    assert "EMAIL FIND:" in capsys.readouterr().out
