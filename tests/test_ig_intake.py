"""An Instagram profile dump, read as Leads and as the corpus it already holds.

Run: python -m pytest tests/test_ig_intake.py -q
 or: python tests/test_ig_intake.py

Two failures already happened on this list shape and both are pinned here.

`intake` returned 0 rows on a dump's own headers and the run continued by
hand-remapping columns, so the first half of this file is about the mapping
being real code with tests rather than an operator's afternoon.

The second half is about the corpus. A profile record carries the account's
recent posts with verbatim captions and real timestamps, which is what `plan`'s
`ig_posts` rung pays for. Ingesting them is only safe if the records are what
they claim: `author=self` proven by a field rather than assumed, a caption
copied rather than tidied, and `retrieved_by` naming the actor that really made
the file.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))
os.environ.setdefault("OUTBOUND_COPY_SOURCE", "csv")

from outbound import ig_intake, observe                       # noqa: E402


def _record(**over) -> dict:
    record = {
        "username": "rita_baki",
        "url": "https://www.instagram.com/rita_baki",
        "fullName": "Rita Baki | Neuro Coach",
        "biography": "I coach you into emotional safety.",
        "externalUrl": "https://linktr.ee/Rita_Baki",
        "externalUrls": [{"url": "https://linktr.ee/Rita_Baki"}],
        "latestPosts": [{
            "caption": "  When we learn the lesson we no longer need it.  ",
            "timestamp": "2026-07-30T16:22:17.000Z",
            "url": "https://www.instagram.com/p/DGlSPUpPfx4/",
            "ownerUsername": "rita_baki",
        }],
    }
    record.update(over)
    return record


# ------------------------------------------------------------------- the lead


def test_the_positioning_suffix_becomes_the_headline_not_the_name():
    """"Rita Baki | Neuro Coach" is a name and a headline, and the wall checks
    the first one. Left joined, every name on the list misses the wall."""
    name, headline = ig_intake.split_display_name("Rita Baki | Neuro Coach")
    assert name == "Rita Baki"
    assert headline == "Neuro Coach"


def test_a_mathematical_bold_name_folds_to_letters():
    """Instagram display names are written in code points that match "Danny
    Jones" nowhere — not on the wall, not in a SERP query, not in a name match.
    """
    name, headline = ig_intake.split_display_name(
        "\U0001d403\U0001d41a\U0001d427\U0001d427\U0001d432 "
        "\U0001d409\U0001d428\U0001d427\U0001d41e\U0001d42c \U0001f1e6\U0001f1ea "
        "| The Performance Coach")
    assert name == "Danny Jones"
    assert headline == "The Performance Coach"


def test_a_name_that_survives_nothing_falls_back_to_the_handle():
    """A row with no name is a row `dedupe` cannot check against the wall, and
    the wall is the one check here that destroys something."""
    name, _ = ig_intake.split_display_name("\U0001f338\U0001f338",
                                           username="sara.coaches")
    assert name == "sara coaches"


def test_every_bio_link_is_read_not_just_the_first():
    """`externalUrls` is an array and 8325744 is the commit that read one of
    it. The extra links land somewhere rather than nowhere."""
    lead = ig_intake.to_lead(_record(externalUrls=[
        {"url": "https://linktr.ee/Rita_Baki"},
        {"url": "https://ritabaki.com"},
        {"url": "https://www.linkedin.com/in/ritabaki"},
    ]))
    assert lead.site_url.startswith("https://ritabaki.com")
    assert "linkedin.com/in/ritabaki" in lead.linkedin_url
    assert any("linktr.ee" in u for u in lead.other_urls)


def test_the_instagram_url_is_kept_as_a_research_target():
    lead = ig_intake.to_lead(_record())
    assert "instagram.com/rita_baki" in lead.instagram_url
    assert lead.has_research_target()


def test_a_scraped_category_of_the_string_none_is_not_a_headline():
    """The scraper writes the literal "None" as often as it writes null."""
    lead = ig_intake.to_lead(_record(fullName="Sara", businessCategoryName="None"))
    assert "none" not in lead.headline.lower()


# ------------------------------------------------------------ the observations


def test_a_post_becomes_an_observation_that_passes_the_gate():
    obs = ig_intake.to_observations(_record(), lead_key="rita|")
    posts = [o for o in obs if o.kind == "post"]
    assert len(posts) == 1
    assert posts[0].published_at == "2026-07-30"
    assert posts[0].author == "self"
    assert posts[0].retrieved_by == "apify:ig_profile"
    assert not observe.validate_all(obs)


def test_the_caption_is_verbatim_including_its_own_whitespace():
    """A summarised observation ranks fine and produces a hook whose quote is
    not on the page. Nothing here tidies one."""
    obs = ig_intake.to_observations(_record(), lead_key="rita|")
    post = next(o for o in obs if o.kind == "post")
    assert post.text == "  When we learn the lesson we no longer need it.  "


def test_somebody_elses_post_on_their_grid_is_dropped():
    """Ban #7 — no third-party coverage — as a field comparison rather than a
    sentence an agent is asked to remember."""
    obs = ig_intake.to_observations(
        _record(latestPosts=[{"caption": "Look who joined us",
                              "timestamp": "2026-07-30T10:00:00.000Z",
                              "url": "https://www.instagram.com/p/X/",
                              "ownerUsername": "somebody_else"}]),
        lead_key="rita|")
    assert [o for o in obs if o.kind == "post"] == []


def test_a_post_with_no_caption_is_not_an_observation():
    """An image with no words is not a quote."""
    obs = ig_intake.to_observations(
        _record(latestPosts=[{"caption": "", "timestamp": "2026-07-30T10:00:00.000Z",
                              "url": "https://www.instagram.com/p/X/",
                              "ownerUsername": "rita_baki"}]),
        lead_key="rita|")
    assert [o for o in obs if o.kind == "post"] == []


def test_the_biography_is_kept_as_its_own_observation():
    obs = ig_intake.to_observations(_record(), lead_key="rita|")
    bio = [o for o in obs if o.kind == "bio"]
    assert len(bio) == 1
    assert bio[0].text.startswith("I coach you")


def test_a_profile_with_no_posts_is_still_a_lead():
    """A quiet or private account is a lead with no corpus. That is something
    `triage` reads and this stage does not judge."""
    lead = ig_intake.to_lead(_record(latestPosts=[], private=True))
    obs = ig_intake.to_observations(_record(latestPosts=[], private=True),
                                    lead_key="rita|")
    assert lead.name == "Rita Baki"
    assert [o for o in obs if o.kind == "post"] == []


def test_the_whole_file_round_trips_and_the_key_is_fetchs():
    """Observations join to leads on `fetch.lead_key`, which is the one
    definition. A handle would have been the obvious local answer and would
    have joined to nothing."""
    from outbound.fetch import lead_key

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write('[' + __import__("json").dumps(_record()) + ']')
        path = handle.name
    leads, observations = ig_intake.ingest(path, source="test")
    assert len(leads) == 1
    assert observations and observations[0].lead_key == lead_key(leads[0])
    shape = ig_intake.profile(leads, observations)
    assert shape["with_observations"] == 1
    assert shape["no_posts"] == 0


def test_a_dump_that_is_not_an_array_is_refused():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write('{"username": "rita_baki"}')
        path = handle.name
    try:
        ig_intake.load_dump(path)
    except ValueError:
        return
    raise AssertionError("a dict is not an Apify dataset and must not read as one")


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)
