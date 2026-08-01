"""Ownership, typed: which channels are plausibly a lead's own.

Run: python -m pytest tests/test_resolve.py -q
 or: python tests/test_resolve.py

Every test here pins a rule that would otherwise regress silently, and the two
at the top pin the same asymmetry the rest of this machine runs on: `unknown`
means no tell was available, never that the tell said no. A stage that reports
false negatives is a stage people learn to scroll past, which is the failure the
existing OWNER-CHECK line was built to fix.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Standalone runs get no conftest, and the link-in-bio path writes ledger lines.
os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

from outbound import fetch, normalize, observe, resolve


def lead_of(**row):
    """A Lead through the real intake path, so the routing under test is the
    routing that runs."""
    return normalize.map_row({"name": "Sarah Khan", **row})


def site_read(social=None, owner="unknown"):
    read = fetch.SiteRead(domain="coachsite.ae", owner_match=owner)
    read.social = social or {}
    return read


# ---------------------------------------------- unknown is not a name mismatch


def test_an_opaque_channel_id_is_unknown_never_absent():
    """`youtube.com/channel/UC1a2b3c` folds to `ucabc`, which contains no part
    of anybody's name. The note version of this check would have called that a
    mismatch, and every opaque id in a batch would read as a bad row."""
    lead = lead_of(website="https://youtube.com/channel/UC1a2b3cDEFGH")
    channel = resolve.resolve_lead(lead).channels[0]
    assert channel.platform == "youtube"
    assert channel.confidence == "unknown", channel.evidence
    assert channel.handle == ""


def test_a_linkedin_company_page_is_unknown_even_when_it_carries_the_name():
    """Both directions of the same rule: a company slug can contain the coach's
    name and still not be a person, and `li_posts` takes a profile URL."""
    lead = lead_of(website="https://linkedin.com/company/sarah-khan-coaching")
    channel = resolve.resolve_lead(lead).channels[0]
    assert channel.confidence == "unknown"
    assert "not a person" in channel.evidence


def test_a_podcast_show_is_unknown_not_absent():
    """A show id is a hash and a show name is not a person's name."""
    lead = lead_of(website="https://open.spotify.com/show/4abcXYZ")
    channel = resolve.resolve_lead(lead).channels[0]
    assert channel.platform == "podcast" and channel.confidence == "unknown"


def test_a_lead_with_no_name_gets_unknown_not_absent():
    lead = normalize.map_row({"name": "",
                              "instagram": "https://instagram.com/themindsetlab"})
    channel = resolve.resolve_lead(lead).channels[0]
    assert channel.confidence == "unknown"
    assert "no name on the row" in channel.evidence


# ------------------------------------------------------------- the two verdicts


def test_a_handle_carrying_the_name_is_confirmed():
    lead = lead_of(linkedin="https://linkedin.com/in/sarah-khan-coach")
    channel = resolve.resolve_lead(lead).channels[0]
    assert channel.confidence == "confirmed" and "sarah" in channel.evidence


def test_a_handle_carrying_nothing_of_the_name_is_absent():
    """The only path to `absent`: a tell was available and it said no."""
    lead = lead_of(instagram="https://instagram.com/themindsetlab")
    channel = resolve.resolve_lead(lead).channels[0]
    assert channel.confidence == "absent"


def test_a_site_that_names_them_vouches_for_what_it_links():
    """F8's payoff one platform over: their own site's social bar is the
    cheapest attribution available once the site is known to be theirs."""
    lead = lead_of(website="https://coachsite.ae")
    read = site_read({"facebook": "https://facebook.com/themindsetlab"},
                     owner="confirmed")
    channel = resolve.resolve_lead(lead, read).channels[0]
    assert channel.confidence == "confirmed"
    assert "which names them" in channel.evidence


def test_provenance_never_demotes():
    """A coach whose site carries only a brand name would otherwise drag every
    real channel they have to `absent`."""
    lead = lead_of(website="https://coachsite.ae")
    read = site_read({"instagram": "https://instagram.com/sarahkhancoach"},
                     owner="absent")
    channel = resolve.resolve_lead(lead, read).channels[0]
    assert channel.confidence == "confirmed"


# --------------------------------------------------- advisory, never a kill


def test_every_lead_gets_an_identity_including_the_ones_with_nothing():
    """R3 in code. Ownership gates spend, never inclusion."""
    leads = [lead_of(instagram="https://instagram.com/themindsetlab"),
             normalize.map_row({"name": "No Channels", "email": "n@x.ae"})]
    identities = resolve.resolve_all(leads)["identities"]
    assert len(identities) == 2
    assert identities[1].channels == []
    assert identities[1].notes, "a lead with nothing must say so"


def test_the_report_says_it_drops_nobody():
    lead = lead_of(instagram="https://instagram.com/themindsetlab")
    text = resolve.report(resolve.resolve_all([lead])["identities"])
    assert "Advisory" in text and "never a reason to skip" in text


# --------------------------------------------------------------- the join key


def test_the_identity_joins_on_the_lead_key_not_the_slug():
    """`sites.json` is keyed by `fetch.lead_key` — an email, else
    `slug|site_url`. A join on the slug would miss every lead with an address,
    quietly, and produce identities with no site evidence on them."""
    lead = lead_of(email="sarah@coachsite.ae", website="https://coachsite.ae")
    identity = resolve.resolve_lead(lead)
    assert identity.lead_key == fetch.lead_key(lead) == "sarah@coachsite.ae"
    assert identity.lead_key != lead.slug


def test_a_site_read_only_reaches_the_lead_it_belongs_to():
    a = lead_of(name="Sarah Khan", email="sarah@x.ae",
                website="https://coachsite.ae")
    b = lead_of(name="Omar Aziz", email="omar@x.ae")
    reads = {fetch.lead_key(a): site_read(
        {"instagram": "https://instagram.com/brandname"}, owner="confirmed")}
    identities = resolve.resolve_all([a, b], reads)["identities"]
    assert identities[0].owner_verdict == "confirmed"
    assert identities[1].owner_verdict == "unknown" and not identities[1].channels


# ------------------------------------------------------------------ the schema


def test_a_verdict_with_no_evidence_is_a_schema_violation():
    """`research`'s rule applied to ownership: a hard verdict naming no source
    was reasoned rather than checked."""
    identity = resolve.Identity(lead_key="a@x.ae", channels=[
        resolve.Channel(platform="linkedin", url="https://linkedin.com/in/x",
                        confidence="confirmed", evidence="")])
    assert any("no evidence" in p for p in resolve.validate(identity))


def test_an_unknown_needs_no_evidence():
    identity = resolve.Identity(lead_key="a@x.ae", channels=[
        resolve.Channel(platform="linkedin", url="https://linkedin.com/in/x",
                        confidence="unknown", evidence="")])
    assert resolve.validate(identity) == []


def test_the_enums_are_enforced():
    identity = resolve.Identity(lead_key="a@x.ae", owner_verdict="maybe",
                                channels=[resolve.Channel(
                                    platform="myspace", url="https://x.ae",
                                    confidence="probably", source="guess",
                                    evidence="x")])
    problems = resolve.validate(identity)
    assert len(problems) == 4, problems


def test_an_identity_with_no_lead_key_is_rejected():
    assert any("lead_key" in p
               for p in resolve.validate(resolve.Identity(name="Sarah")))


def test_the_same_channel_cannot_be_counted_twice():
    identity = resolve.Identity(lead_key="a@x.ae", channels=[
        resolve.Channel(platform="linkedin", url="https://linkedin.com/in/x",
                        confidence="unknown"),
        resolve.Channel(platform="linkedin", url="https://linkedin.com/in/x",
                        confidence="unknown")])
    assert any("repeats" in p for p in resolve.validate(identity))


def test_a_channel_found_twice_is_merged_at_the_strongest_verdict():
    """The row and the site harvest overlap constantly. Strongest wins rather
    than first-seen, so arrival order cannot change a verdict."""
    lead = lead_of(linkedin="https://linkedin.com/in/sarah-khan-coach",
                   website="https://coachsite.ae")
    read = site_read({"linkedin": "https://www.linkedin.com/in/sarah-khan-coach/"})
    channels = resolve.resolve_lead(lead, read).channels
    assert len([c for c in channels if c.platform == "linkedin"]) == 1
    assert channels[0].confidence == "confirmed"


def test_validate_all_says_which_identity_was_wrong():
    problems = resolve.validate_all(
        [resolve.Identity(lead_key="a@x.ae"), resolve.Identity()])
    assert problems and problems[0].startswith("identity[1]")


def test_from_dict_drops_unknown_keys_and_coerces_null():
    identity = resolve.Identity.from_dict({
        "lead_key": "a@x.ae", "channels": None, "notes": None, "spam": 1})
    assert identity.channels == [] and identity.notes == []


def test_load_accepts_the_file_the_command_writes():
    lead = lead_of(instagram="https://instagram.com/sarahkhan")
    written = {"identities":
               [i.to_dict() for i in resolve.resolve_all([lead])["identities"]]}
    assert resolve.load(written)[0].channels[0].confidence == "confirmed"


def test_schema_help_is_generated_from_the_dataclass():
    text = resolve.schema_help()
    assert "owner_verdict" in text and "confidence" in text
    assert "never means the tell said no" in text


def test_the_platform_vocabulary_is_observe_s():
    """Widened, not mapped. A translation table between two platform enums is a
    value copied out of its authority."""
    assert resolve.PLATFORMS is observe.PLATFORMS
    assert "linkinbio" in observe.PLATFORMS and "twitter" in observe.PLATFORMS


# --------------------------------------------------------------- the delegation


def test_the_intake_note_and_the_typed_verdict_agree():
    """`_profile_name_notes` is the prose presentation of the same rule, not a
    second implementation — and it inherited the opaque-id guard by delegating,
    which the local version could not do."""
    mismatched = lead_of(instagram="https://instagram.com/themindsetlab")
    assert any("Instagram handle does not contain" in n for n in mismatched.notes)
    assert resolve.resolve_lead(mismatched).channels[0].confidence == "absent"

    matched = lead_of(instagram="https://instagram.com/sarahkhan")
    assert not any("does not contain" in n for n in matched.notes)


# --------------------------------------------------------- the standalone path

if __name__ == "__main__":
    import inspect

    failures = 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        if inspect.signature(fn).parameters:
            print(f"SKIP {name} (needs a pytest fixture)")
            continue
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)
