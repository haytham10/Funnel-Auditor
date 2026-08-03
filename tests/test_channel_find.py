"""A lead's own channels, picked out of search results.

Run: python -m pytest tests/test_channel_find.py -q
 or: python tests/test_channel_find.py

This file is mostly about the URLs that must NOT be accepted.

A wrong address bounces and `email-verify` catches it. A wrong LinkedIn URL
verifies clean, scrapes clean and produces a real, re-fetchable, quotable hook
about a real person who is not the lead — `hook`, `hook-verifier` and `lint` all
check the content and none of them checks whose. So the interesting cases here
are the near misses: a different person with the same name, a company page, a
directory listing, and a result that names the lead while pointing at somebody
else's profile.

The Arabic-name case is not decorative. 228 of the 311 names on the list this
was built for are two tokens, and a search for a common one returns ten real
people, several of them coaches, several of them in Dubai.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))
os.environ.setdefault("OUTBOUND_COPY_SOURCE", "csv")

from audit import channel_find                                # noqa: E402
from outbound import resolve                                  # noqa: E402


def serp(*rows) -> dict:
    """One actor record, in the shape `google_search` returns."""
    return {"searchQuery": {"term": "q"},
            "organicResults": [dict(r) for r in rows]}


def row(url, title="", description="") -> dict:
    return {"url": url, "title": title, "description": description}


# ------------------------------------------------------------ the easy yes


def test_a_handle_carrying_the_whole_name_is_accepted():
    result = channel_find.find_channels(
        "Charmaine Klima",
        serp(row("https://www.linkedin.com/in/charmaineklima/",
                 "Charmaine Klima - Executive Coach", "Dubai, UAE")))
    assert result["verdict"] == "FOUND"
    assert result["accepted"]["linkedin_url"] == "https://linkedin.com/in/charmaineklima"
    assert result["candidates"][0]["tier"] == "handle"


def test_a_site_whose_domain_is_the_name_is_accepted():
    result = channel_find.find_channels(
        "Cindy Vandekreke", serp(row("https://cindyvandekreke.com/about", "About")))
    assert result["accepted"]["site_url"] == "https://cindyvandekreke.com"
    assert result["candidates"][0]["tier"] == "handle"


def test_a_hyphenated_linkedin_slug_still_matches():
    result = channel_find.find_channels(
        "Dana Zaarour",
        serp(row("https://www.linkedin.com/in/dana-zaarour/", "Dana Zaarour")))
    assert result["accepted"]["linkedin_url"] == "https://linkedin.com/in/dana-zaarour"


# ---------------------------------------------------- the expensive near miss


def test_a_common_name_with_an_opaque_slug_is_not_accepted_on_circumstance():
    """The Arabic-collision case. The result names him, says Dubai and says
    coach — and the URL carries nothing of his name. That is the exact shape of
    a stranger's profile on a page that mentions the lead."""
    result = channel_find.find_channels(
        "Mohammed Ali",
        serp(row("https://www.linkedin.com/in/7a3b2c1d9/",
                 "Mohammed Ali - Executive Coach - Dubai",
                 "Mohammed Ali is an ICF coach based in Dubai, UAE.")))
    assert result["verdict"] == "UNCORROBORATED"
    assert result["accepted"]["linkedin_url"] == ""
    assert result["unrelated"], "the drop must stay visible"


def test_naming_the_lead_alone_never_corroborates():
    """`email_find` learned this at the cost of four false positives: a page
    being about somebody corroborates the page, not everything printed on it."""
    result = channel_find.find_channels(
        "Sarah Khan",
        serp(row("https://www.linkedin.com/in/dubaicoachingcollective/",
                 "Dubai Coaching Collective",
                 "Sarah Khan speaks at our Dubai event. ICF coach.")))
    assert result["verdict"] == "UNCORROBORATED"
    assert "not their channel" in result["unrelated"][0]["why"] \
        or "no part of their name" in result["unrelated"][0]["why"]


def test_a_partial_handle_plus_a_vouching_result_is_the_corroborated_tier():
    """Rule 4: the handle carries part of the name AND the result names them in
    full AND places them. Two independent properties, which is the fix."""
    result = channel_find.find_channels(
        "Aleksandra Pavlovic",
        serp(row("https://www.linkedin.com/in/aleksandra-p-coaching/",
                 "Aleksandra Pavlovic - Leadership Coach",
                 "Aleksandra Pavlovic, ICF PCC, based in Dubai.")))
    assert result["verdict"] == "FOUND"
    assert result["candidates"][0]["tier"] == "corroborated"


def test_a_partial_handle_without_a_vouching_result_is_dropped():
    result = channel_find.find_channels(
        "Aleksandra Pavlovic",
        serp(row("https://www.linkedin.com/in/aleksandra-p-coaching/",
                 "Aleksandra P.", "Coaching services.")))
    assert result["verdict"] == "UNCORROBORATED"


# ------------------------------------------------------------- the ambiguity
#
# The pilot's finding, and the most expensive bug this module had. Six of
# fourteen FOUND leads came back with two or three LinkedIn profiles all
# carrying the name, and the first was silently kept.


def test_two_people_of_the_same_name_are_not_a_find():
    """`Gitanjali Sharma` returned three generated slugs belonging to three
    different real people. Keeping the first is a one-in-three guess shipped as
    a confirmed channel."""
    result = channel_find.find_channels(
        "Gitanjali Sharma",
        serp(row("https://www.linkedin.com/in/gitanjali-sharma-865322171/",
                 "Gitanjali Sharma"),
             row("https://www.linkedin.com/in/gitanjali-sharma-a19808384/",
                 "Gitanjali Sharma"),
             row("https://www.linkedin.com/in/gitanjali-sharma-aa8579201/",
                 "Gitanjali Sharma")))
    assert result["verdict"] == "AMBIGUOUS"
    assert result["accepted"]["linkedin_url"] == ""
    assert "coin flip" in result["reason"]
    # The competitors stay visible — a human settles this in thirty seconds.
    assert len(result["candidates"]) == 3


def test_the_vanity_slug_breaks_a_tie():
    """`linkedin.com/in/melbaxter` is a slug its owner claimed;
    `mel-baxter-a2273277` is one LinkedIn generated because it was taken."""
    result = channel_find.find_channels(
        "Mel Baxter",
        serp(row("https://www.linkedin.com/in/mel-baxter-a2273277/", "Mel Baxter"),
             row("https://www.linkedin.com/in/melbaxter/", "Mel Baxter")))
    assert result["verdict"] == "FOUND"
    assert result["accepted"]["linkedin_url"] == "https://linkedin.com/in/melbaxter"


def test_a_locale_suffix_is_the_same_profile_not_a_rival():
    """`/in/ramisukkar/fr` and `/in/ramisukkar` are one person. Without the
    truncation they arrive as two candidates and one real profile reads as an
    ambiguity."""
    result = channel_find.find_channels(
        "Rami Sukkar",
        serp(row("https://www.linkedin.com/in/ramisukkar/fr", "Rami Sukkar"),
             row("https://www.linkedin.com/in/ramisukkar", "Rami Sukkar")))
    assert result["verdict"] == "FOUND"
    assert result["accepted"]["linkedin_url"] == "https://linkedin.com/in/ramisukkar"
    assert len(result["candidates"]) == 1


def test_an_ambiguity_on_one_platform_does_not_blank_another():
    result = channel_find.find_channels(
        "Mel Baxter",
        serp(row("https://www.linkedin.com/in/mel-baxter-1234/", "Mel Baxter"),
             row("https://www.linkedin.com/in/mel-baxter-5678/", "Mel Baxter"),
             row("https://www.instagram.com/melbaxter/", "Mel Baxter")))
    assert result["accepted"]["linkedin_url"] == ""
    assert result["accepted"]["instagram_url"] == "https://instagram.com/melbaxter"
    assert result["verdict"] == "FOUND"
    assert "linkedin" in result["ambiguous"]


def test_the_row_settles_an_ambiguity_the_search_could_not():
    result = channel_find.find_channels(
        "Mel Baxter",
        serp(row("https://www.linkedin.com/in/mel-baxter-1234/", "Mel Baxter"),
             row("https://www.linkedin.com/in/mel-baxter-5678/", "Mel Baxter")),
        known={"linkedin_url": "https://linkedin.com/in/the-real-mel"})
    assert result["accepted"]["linkedin_url"] == "https://linkedin.com/in/the-real-mel"
    assert result["ambiguous"] == {}
    assert result["from_row"] == ["linkedin_url"]


def test_a_row_supplied_channel_the_search_confirms_is_still_found():
    """An earlier cut excluded row-supplied fields from the verdict, so a lead
    whose row carried a LinkedIn the search then confirmed came back
    UNCORROBORATED while holding a verified URL."""
    result = channel_find.find_channels(
        "Charmaine Klima",
        serp(row("https://www.linkedin.com/in/charmaineklima/", "Charmaine Klima")),
        known={"linkedin_url": "https://linkedin.com/in/charmaineklima"})
    assert result["verdict"] == "FOUND"


# ------------------------------------------------- structurally not a channel


def test_a_linkedin_company_page_is_never_a_person():
    result = channel_find.find_channels(
        "Sarah Khan",
        serp(row("https://www.linkedin.com/company/sarah-khan-coaching/",
                 "Sarah Khan Coaching", "Dubai ICF coach")))
    assert result["accepted"]["linkedin_url"] == ""
    assert result["verdict"] == "UNCORROBORATED"


def test_instagram_posts_and_app_paths_are_not_accounts():
    for url in ("https://www.instagram.com/p/DGlSPUpPfx4/",
                "https://www.instagram.com/reel/DGlSPUpPfx4/",
                "https://www.instagram.com/explore/people/",
                "https://www.instagram.com/accounts/login/"):
        result = channel_find.find_channels(
            "Sarah Khan", serp(row(url, "Sarah Khan", "Dubai coach")))
        assert result["accepted"]["instagram_url"] == "", url


def test_the_icf_directory_is_never_the_lead_own_site():
    """The source that produced the list must not come back as the thing it
    enriches — every ICF listing names the coach in full."""
    result = channel_find.find_channels(
        "Sarah Khan",
        serp(row("https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx"
                 "?coachcstkey=ABC", "Sarah Khan - ICF Credentialed Coach",
                 "Sarah Khan, PCC, Dubai, UAE")))
    assert result["accepted"]["site_url"] == ""


def test_a_profile_that_states_a_foreign_location_is_a_different_person():
    """The live run's clearest false positive. `madeleine-scott-956a6a20`
    carried her name exactly and belonged to a Dance Professor Emerita in
    Athens, Ohio. Every lead on a UAE directory is in the UAE."""
    result = channel_find.find_channels(
        "Madeleine Scott",
        serp(row("https://www.linkedin.com/in/madeleine-scott-956a6a20/",
                 "Madeleine Scott - Professor Emerita, Dance",
                 "Experience: Ohio University · Education: UCLA · "
                 "Location: Athens · 96 connections")))
    assert result["accepted"]["linkedin_url"] == ""
    assert "not the UAE" in result["unrelated"][0]["why"]


def test_an_arabic_location_is_the_uae():
    """`google_search` runs with countryCode=ae, so Google renders a UAE
    person's location in Arabic. Six of the nine live profiles that stated a
    location at all stated it this way, and an ASCII-only word list read every
    one as "does not say UAE"."""
    result = channel_find.find_channels(
        "Farideh Niknejad",
        serp(row("https://www.linkedin.com/in/farideh-niknejad-425625366/",
                 "Farideh Niknejad", "الموقع: دبي · ICF PCC")))
    assert result["accepted"]["linkedin_url"] != ""


def test_a_missing_location_is_never_a_demotion():
    """It fires on a stated location and never on a missing one — `resolve`'s
    rule 4, where only an available tell may say no."""
    result = channel_find.find_channels(
        "Charmaine Klima",
        serp(row("https://www.linkedin.com/in/charmaineklima/", "Charmaine Klima")))
    assert result["accepted"]["linkedin_url"] != ""


def test_a_path_segment_on_somebody_elses_domain_is_not_a_handle():
    """The live run's worst bug. `_candidate` computed a handle for site
    candidates out of the URL path, so `idcrawl.com/christine-harb` folded to
    `christineharb`, matched her name exactly, and was accepted at the strongest
    tier. A people-search index of a person is not that person's website, and a
    path segment says who a page is ABOUT, never whose channel it is."""
    for url in ("https://idcrawl.com/christine-harb",
                "https://contactout.com/usha-kaul-saraf",
                "https://leagrowingpeople.com/richa-singh"):
        name = url.rsplit("/", 1)[-1].replace("-", " ").title()
        result = channel_find.find_channels(name, serp(row(url, name)))
        assert result["accepted"]["site_url"] == "", url


def test_the_newer_social_networks_are_not_websites():
    """A live SERP over 300 coaches returned every one of these as a candidate
    website."""
    for url in ("https://threads.com/@mariageorgaki",
                "https://x.com/somecoach", "https://skool.com/somecoach",
                "https://topmate.io/richasingh"):
        result = channel_find.find_channels(
            "Maria Georgaki", serp(row(url, "Maria Georgaki")))
        assert result["accepted"]["site_url"] == "", url


def test_a_domain_that_is_their_name_is_still_accepted():
    """The guards above must not swallow the case that works: nine of the real
    list's websites were found exactly this way."""
    result = channel_find.find_channels(
        "Wadad Maalouf", serp(row("https://wadadmaalouf.com/about", "Wadad")))
    assert result["accepted"]["site_url"] == "https://wadadmaalouf.com"


def test_a_page_that_names_and_places_them_is_still_not_their_website():
    """The pilot's clearest finding. For the ten leads with no website, every
    non-platform host the SERP returned was a page that merely mentions them —
    a university catalog, a Scribd PDF, a podcast host, a cat magazine, an HR
    summit — and all of them name the coach in full. A circumstance-only rule
    for sites would have accepted `cats.com` as a coach's website."""
    for host, title in (("https://cats.com/vets", "Dr. Margit Gabriele Muller MRCVS"),
                        ("https://aus.edu/catalog", "Undergraduate Catalog"),
                        ("https://exito-e.com/hr", "HR World Summit UAE 2026")):
        result = channel_find.find_channels(
            "Margit Gabriele Muller",
            serp(row(host, title,
                     "Margit Gabriele Muller, coach, Abu Dhabi, UAE")))
        assert result["accepted"]["site_url"] == "", host


def test_a_link_in_bio_host_is_never_the_lead_own_site():
    result = channel_find.find_channels(
        "Sarah Khan", serp(row("https://linktr.ee/sarahkhan", "Sarah Khan")))
    assert result["accepted"]["site_url"] == ""


# ------------------------------------------------------------- the two blanks


def test_uncorroborated_and_none_are_different_answers():
    """Both leave the field blank. One is a fact about the coach and the other
    is a fact about this filter, and collapsing them would hide which."""
    nothing = channel_find.find_channels("Sarah Khan", serp())
    assert nothing["verdict"] == "NONE"
    assert "no organic result" in nothing["reason"]

    rejected = channel_find.find_channels(
        "Sarah Khan", serp(row("https://www.linkedin.com/in/9f8e7d6/", "Someone")))
    assert rejected["verdict"] == "UNCORROBORATED"
    assert "found and rejected" in rejected["reason"]


def test_a_result_with_no_channel_urls_at_all_is_none():
    result = channel_find.find_channels(
        "Sarah Khan", serp(row("https://news.example.com/article", "Coaching news")))
    # A news site is a `site` candidate structurally, but nothing connects it.
    assert result["accepted"]["site_url"] == ""
    assert result["verdict"] == "UNCORROBORATED"


# ------------------------------------------------------------------ the merge


def test_two_records_for_one_lead_merge_before_ranking():
    """The two-query shape returns two records and the merge has to happen
    before the pick, or the second query's better answer loses to the first."""
    plain = serp(row("https://sarahkhancoaching.ae", "Sarah Khan Coaching"))
    scoped = serp(row("https://www.linkedin.com/in/sarahkhan/", "Sarah Khan"))
    result = channel_find.find_channels("Sarah Khan", [plain, scoped])
    assert result["accepted"]["site_url"] == "https://sarahkhancoaching.ae"
    assert result["accepted"]["linkedin_url"] == "https://linkedin.com/in/sarahkhan"


def test_the_same_channel_twice_is_one_candidate():
    result = channel_find.find_channels(
        "Sarah Khan",
        serp(row("https://www.linkedin.com/in/sarahkhan/", "Sarah Khan"),
             row("https://de.linkedin.com/in/sarahkhan", "Sarah Khan")))
    assert len(result["candidates"]) == 1


def test_a_channel_the_row_already_had_is_never_overwritten():
    """Nine real leads arrived with a LinkedIn in their website column. The row
    is a stronger provenance than anything bought here."""
    result = channel_find.find_channels(
        "Sarah Khan",
        serp(row("https://www.linkedin.com/in/sarahkhan/", "Sarah Khan")),
        known={"linkedin_url": "https://linkedin.com/in/sarah-khan-real"})
    assert result["accepted"]["linkedin_url"] == "https://linkedin.com/in/sarah-khan-real"


# ---------------------------------------------------------------- the queries


def test_the_query_carries_the_city_and_a_known_domain():
    queries = channel_find.build_queries(
        "Sarah Khan", city="Dubai", domains=("https://sarahkhan.ae",))
    assert queries == ['"Sarah Khan" Dubai coach sarahkhan.ae']


def test_a_platform_host_is_never_a_query_term():
    """Searching `linkedin.com` searches for LinkedIn."""
    queries = channel_find.build_queries(
        "Sarah Khan", city="Dubai",
        domains=("https://www.linkedin.com/in/sarahkhan",))
    assert "linkedin.com" not in queries[0]


def test_a_parenthetical_nickname_replaces_the_certificate_name():
    """One real row reads `Catharina (Cindy) Leonarda Maria Van De
    Kreke-Freens`. Seven tokens in quotes finds nothing; she is indexed
    everywhere as Cindy."""
    queries = channel_find.build_queries(
        "Catharina (Cindy) Leonarda Maria Van De Kreke-Freens", city="Dubai")
    assert '"Cindy Leonarda Maria Van De Kreke-Freens"' in queries[0]
    assert "Catharina" not in queries[0]


def test_the_two_query_shape_scopes_the_second_to_linkedin_people():
    queries = channel_find.build_queries("Sarah Khan", city="Dubai", shape="two")
    assert len(queries) == 2
    assert queries[1].startswith("site:linkedin.com/in")


def test_a_nameless_lead_produces_no_query():
    assert channel_find.build_queries("") == []


# ------------------------------------------------------- handing over to resolve


def test_to_channels_produces_channels_resolve_accepts():
    """The test that would fail before `serp` joined `resolve.SOURCES`."""
    result = channel_find.find_channels(
        "Charmaine Klima",
        serp(row("https://www.linkedin.com/in/charmaineklima/", "Charmaine Klima")))
    channels = channel_find.to_channels("Charmaine Klima", result)
    identity = resolve.Identity(
        lead_key="a@x.ae", name="Charmaine Klima",
        channels=[resolve.Channel(**c) for c in channels])
    assert resolve.validate(identity) == []
    assert channels[0]["source"] == "serp"


def test_resolve_is_allowed_to_disagree_with_a_corroborated_tier():
    """This module accepts on circumstance the handle does not support.
    Overwriting `resolve`'s verdict would hide the weaker tier from every
    reader downstream."""
    result = channel_find.find_channels(
        "Aleksandra Pavlovic",
        serp(row("https://www.linkedin.com/in/aleksandra-p-coaching/",
                 "Aleksandra Pavlovic - Leadership Coach",
                 "Aleksandra Pavlovic, ICF PCC, based in Dubai.")))
    channel = channel_find.to_channels("Aleksandra Pavlovic", result)[0]
    assert channel["confidence"] in resolve.CONFIDENCE
    assert "corroborated" in channel["evidence"]


def test_a_site_is_not_a_resolve_channel():
    result = channel_find.find_channels(
        "Cindy Vandekreke", serp(row("https://cindyvandekreke.com", "Cindy")))
    assert channel_find.to_channels("Cindy Vandekreke", result) == []


# ------------------------------------------------------------ never fetches


def test_this_module_does_not_import_the_paid_layer():
    """`footprint`'s property: when the fetch layer under a module like this
    was retired, being fetch-agnostic made it a deletion, not a rewrite."""
    source = Path(channel_find.__file__).read_text(encoding="utf-8")
    assert "import apify" not in source
    assert "from audit.apify" not in source
    assert "requests" not in source


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
