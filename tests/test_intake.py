"""Intake and dedupe: the two cheap stages that run before anything is spent.

Run: python -m pytest tests/test_intake.py -q
 or: python tests/test_intake.py

The dedupe tests carry the highest stakes in the repo. A cold opener landing on
a live warm thread is the only failure here that destroys something rather than
wasting something, and it has already happened twice.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import dedupe, normalize


# -------------------------------------------------------------- site verdicts


def test_a_real_domain_is_an_own_site():
    verdict = normalize.classify_site("https://www.sarahcoaching.ae/")
    assert verdict.verdict == "own_site"
    assert verdict.url == "https://sarahcoaching.ae"


def test_a_bare_domain_gets_a_scheme():
    assert normalize.classify_site("sarahcoaching.ae").verdict == "own_site"


def test_a_linkedin_url_is_a_research_target_not_junk():
    """24 rows were discarded for this on the last list. A platform URL in the
    website column points at the best research surface on the row."""
    verdict = normalize.classify_site("https://linkedin.com/in/sarah-coach")
    assert verdict.verdict == "platform"
    assert verdict.platform == "linkedin"
    assert verdict.is_research_target()


def test_a_linktree_is_a_platform_too():
    assert normalize.classify_site("https://linktr.ee/sarahcoach").platform == "linkinbio"


def test_a_podcast_show_is_a_platform():
    """Rung 2 of the hook ladder had no host list at all, so a Spotify show in
    the website column was fetched as an own site — a JS app that returns 200
    with no text, which routes it into the render escalation, the most expensive
    rung there is, on a page that can never yield anything."""
    for url in ("https://open.spotify.com/show/4abcXYZ",
                "https://anchor.fm/sarahcoach",
                "https://podcasts.apple.com/ae/podcast/the-coach/id1234"):
        assert normalize.classify_site(url).platform == "podcast", url


def test_apple_is_not_a_podcast_host_but_apple_podcasts_is():
    """`registrable_domain("podcasts.apple.com")` is `apple.com`. Keying the map
    on the registrable domain alone would have labelled every Apple URL a
    podcast, so `classify_site` matches the host too."""
    assert normalize.classify_site("https://apple.com/store").verdict == "own_site"
    assert normalize.classify_site(
        "https://podcasts.apple.com/us/podcast/x/id9").platform == "podcast"


def test_a_bare_platform_root_is_junk():
    """instagram.com with no handle tells us nothing about anyone."""
    assert normalize.classify_site("https://instagram.com").verdict == "junk"


def test_a_parked_domain_is_parked():
    assert normalize.classify_site("http://hugedomains.com/x").verdict == "parked"


def test_a_real_domain_that_merely_contains_a_parker_name_survives():
    """`"dan.com" in host` matched jordan.com and sudan.com; `"sav.com"`
    matched coachsav.com. Real coach domains, dropped as for-sale before any
    research ran — the same silent loss the platform routing exists to stop."""
    for url in ("https://jordan.com", "https://sudan.com",
                "https://coachsav.com", "https://mydan.com"):
        assert normalize.classify_site(url).verdict == "own_site", url


def test_infrastructure_urls_are_junk():
    for url in ("https://accounts.google.com/signin",
                "https://outlook.live.com/mail",
                "https://calendly.com/someone"):
        assert normalize.classify_site(url).verdict == "junk", url


def test_an_image_file_is_junk():
    assert normalize.classify_site("https://site.com/logo.png").verdict == "junk"


def test_missing_and_placeholder_values_are_missing():
    for value in ("", "  ", "N/A", "none", "-"):
        assert normalize.classify_site(value).verdict == "missing", repr(value)


# ------------------------------------------------------------------- mapping


def test_headers_map_across_common_spellings():
    lead = normalize.map_row({
        "Full Name": "Sarah Al-Mansouri",
        "Website URL": "sarahcoaching.ae",
        "Email Address": "sarah@sarahcoaching.ae",
        "LinkedIn": "https://linkedin.com/in/sarah",
        "Location": "Dubai",
    })
    assert lead.name == "Sarah Al-Mansouri"
    assert lead.first_name == "Sarah"
    assert lead.email == "sarah@sarahcoaching.ae"
    assert lead.city == "Dubai"
    assert lead.domain == "sarahcoaching.ae"


def test_a_platform_url_in_the_site_column_fills_the_social_field():
    lead = normalize.map_row({"Name": "Sarah", "Website": "https://instagram.com/sarahcoach"})
    assert lead.site_url == ""
    assert lead.instagram_url == "https://instagram.com/sarahcoach"
    assert lead.has_research_target()


def test_a_sales_export_names_the_site_after_the_company():
    """The first real list used `companyWebsite` and mapped ZERO of 13 sites.
    Every lead fell through to social-only research and the entire free
    site-read tier was skipped, with nothing printed to say so."""
    for header in ("companyWebsite", "Company URL", "company_domain",
                   "Business Website", "Web URL", "Domain Name"):
        lead = normalize.map_row({"Full Name": "Sarah", header: "sarahcoaching.ae"})
        assert lead.site_url, header
        assert lead.domain == "sarahcoaching.ae", header


def test_unmapped_columns_are_reported_not_just_dropped():
    """Dropping an unknown column is right; dropping it silently is how the
    website column went missing for a whole batch."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "raw.csv"
        path.write_text("Full Name,companyHeadCount,bucket\nSarah,25,x\n",
                        encoding="utf-8")
        ignored = normalize.unmapped_headers(str(path))
        assert "companyHeadCount" in ignored and "bucket" in ignored
        assert "Full Name" not in ignored


def test_a_platform_with_no_dedicated_field_lands_in_other_urls():
    """Six of the ten PLATFORM_HOSTS had no field to route into, so
    `classify_site` correctly called them research targets and `map_row` then
    threw them away — leaving the lead counted as having nothing to work."""
    for url in ("https://tiktok.com/@sarahcoach",
                "https://x.com/sarahcoach",
                "https://linktr.ee/sarahcoach",
                "https://stan.store/sarahcoach"):
        lead = normalize.map_row({"Name": "Sarah", "Website": url})
        assert lead.other_urls == [url], url
        assert lead.social_urls() == [url]
        assert lead.has_research_target()


def test_an_explicit_social_column_wins_over_the_site_column():
    lead = normalize.map_row({
        "Name": "Sarah",
        "Website": "https://linkedin.com/in/from-site-column",
        "LinkedIn": "https://linkedin.com/in/explicit",
    })
    assert lead.linkedin_url == "https://linkedin.com/in/explicit"


def test_a_dead_site_with_a_social_profile_still_has_a_target():
    """199 of 336 rows had a dead or missing site. A hard site gate was
    throwing away most of the market."""
    lead = normalize.map_row({"Name": "Sarah", "Website": "hugedomains.com/x",
                              "Instagram": "https://instagram.com/sarahcoach"})
    assert lead.site_url == ""
    assert lead.has_research_target()


def test_a_lead_with_nothing_at_all_has_no_target():
    lead = normalize.map_row({"Name": "Sarah", "Website": "N/A"})
    assert not lead.has_research_target()


def test_names_split_and_rejoin():
    assert normalize.map_row({"First": "Sarah", "Last": "Khan"}).name == "Sarah Khan"
    assert normalize.map_row({"Name": "Sarah Khan"}).last_name == "Khan"


def test_profile_counts_the_batch():
    leads = [
        normalize.map_row({"Name": "A", "Website": "a.ae", "Email": "a@a.ae"}),
        normalize.map_row({"Name": "B", "Instagram": "https://instagram.com/b"}),
        normalize.map_row({"Name": "C", "Website": "N/A"}),
    ]
    shape = normalize.profile(leads)
    assert shape == {"total": 3, "with_site": 1, "social_only": 1,
                     "with_email": 1, "no_research_target": 1,
                     "parked_names": ["C"]}


# ------------------------------------------------------------------- name keys


def test_reordered_names_collapse_to_one_key():
    assert dedupe.name_key("Sarah Al-Mansouri") == dedupe.name_key("Al Mansouri, Sarah")


def test_titles_and_accents_are_stripped():
    assert dedupe.name_key("Dr. Sarah Khan") == dedupe.name_key("sarah khan")
    assert dedupe.name_key("José Álvarez") == dedupe.name_key("Jose Alvarez")


def test_different_people_keep_different_keys():
    assert dedupe.name_key("Sarah Khan") != dedupe.name_key("Sara Khan")


def test_the_same_tokens_in_a_different_order_are_different_people():
    """The strict key preserves order. Sorting it merged "Ahmed Mohammed Ali"
    with "Ali Mohammed Ahmed" — three different men in a market where given
    names double as surnames, and a permanent invisible kill for two of them."""
    keys = {dedupe.name_key(n) for n in
            ("Ahmed Mohammed Ali", "Ali Mohammed Ahmed", "Mohammed Ahmed Ali")}
    assert len(keys) == 3


def test_the_loose_key_still_sees_through_an_inversion():
    assert (dedupe.loose_name_key("Ahmed Mohammed Ali")
            == dedupe.loose_name_key("Ali Mohammed Ahmed"))


def test_a_reordered_cold_contact_is_an_echo_not_a_kill():
    """The uncertain case resolves toward the recoverable error: a second cold
    email months apart wastes a send, a false kill loses the lead forever."""
    wall = dedupe.ContactWall.from_records(
        [{"Contact Name": "Ahmed Mohammed Ali", "Status": "Outreach Sent"}])
    lead = normalize.map_row({"Name": "Ali Mohammed Ahmed"})
    result = dedupe.check_early(lead, wall)
    assert isinstance(result, dedupe.NameEcho)
    assert "check it is not the same person" in result.line()


def test_a_reordered_warm_contact_does_stop_the_run():
    """The other direction. A cold opener on a live thread destroys something
    rather than wasting something, so the uncertain case stops here."""
    wall = dedupe.ContactWall.from_records(
        [{"Contact Name": "Rita Baki", "Status": "Reply Received"}])
    hit = dedupe.check_early(normalize.map_row({"Name": "Baki Rita"}), wall)
    assert isinstance(hit, dedupe.DupeHit)
    assert hit.warm and hit.matched_on == "name (reordered)"


def test_an_echo_still_ships_and_is_reported():
    wall = dedupe.ContactWall.from_records(
        [{"Contact Name": "Ahmed Mohammed Ali", "Status": "Outreach Sent"}])
    result = dedupe.partition([normalize.map_row({"Name": "Ali Mohammed Ahmed"})], wall)
    assert len(result["clear"]) == 1
    assert len(result["dupes"]) == 0
    assert len(result["echoes"]) == 1
    assert any("look" in line for line in dedupe.report(result))


def test_gmail_dots_and_tags_are_the_same_mailbox():
    assert dedupe.email_key("s.a.r.a.h+coach@gmail.com") == "sarah@gmail.com"


def test_dots_matter_outside_gmail():
    assert dedupe.email_key("s.arah@site.ae") == "s.arah@site.ae"


# ---------------------------------------------------------------- the wall


def wall():
    return dedupe.ContactWall.from_records([
        {"Contact Name": "Sarah Al-Mansouri", "Email": "sarah@old.ae",
         "Site URL": "https://sarahcoaching.ae", "Status": "Outreach Sent"},
        {"Contact Name": "Lisa Hugo", "Email": "lisa@hugo.ae",
         "Status": "Reply Received"},
    ])


def test_a_previously_contacted_name_is_caught_early():
    lead = normalize.map_row({"Name": "Al Mansouri, Sarah"})
    hit = dedupe.check_early(lead, wall())
    assert hit and hit.matched_on == "name"


def test_a_previously_contacted_domain_is_caught_early():
    lead = normalize.map_row({"Name": "Someone Else", "Website": "sarahcoaching.ae"})
    hit = dedupe.check_early(lead, wall())
    assert hit and hit.matched_on == "domain"


def test_a_married_name_is_missed_early_and_caught_late():
    """Exactly why there are two passes. Pass 1 cannot see a name change; pass
    2 catches it once research has found the address."""
    lead = normalize.map_row({"Name": "Sarah Ahmed", "Email": "sarah@old.ae"})
    assert dedupe.check_early(lead, wall()) is None
    hit = dedupe.check_late(lead, wall())
    assert hit and hit.matched_on == "email"


def test_a_live_thread_is_flagged_warm():
    lead = normalize.map_row({"Name": "Lisa Hugo"})
    hit = dedupe.check_early(lead, wall())
    assert hit and hit.warm
    assert "WARM THREAD" in hit.line()


def test_an_ordinary_duplicate_is_not_warm():
    lead = normalize.map_row({"Name": "Sarah Al-Mansouri"})
    assert not dedupe.check_early(lead, wall()).warm


def test_a_fresh_lead_passes():
    lead = normalize.map_row({"Name": "Nobody New", "Website": "brandnew.ae"})
    assert dedupe.check_early(lead, wall()) is None


# ------------------------------------------------------------------ partition


def test_partition_separates_warm_from_ordinary_dupes():
    leads = [
        normalize.map_row({"Name": "Nobody New", "Website": "new.ae"}),
        normalize.map_row({"Name": "Sarah Al-Mansouri"}),
        normalize.map_row({"Name": "Lisa Hugo"}),
    ]
    result = dedupe.partition(leads, wall())
    assert len(result["clear"]) == 1
    assert len(result["dupes"]) == 2
    assert len(result["warm_hits"]) == 1


def test_duplicates_inside_one_batch_are_caught():
    """7 of 50 survivors were the same people from two overlapping directories.
    Two coaches receiving the same email is the tell it was generated."""
    leads = [
        normalize.map_row({"Name": "New Person", "Website": "a.ae"}),
        normalize.map_row({"Name": "Person, New", "Website": "b.ae"}),
    ]
    result = dedupe.partition(leads, dedupe.ContactWall())
    assert len(result["clear"]) == 1
    assert len(result["internal"]) == 1


def test_the_report_names_every_warm_hit():
    leads = [normalize.map_row({"Name": "Lisa Hugo"})]
    lines = dedupe.report(dedupe.partition(leads, wall()))
    assert any("STOP" in line and "Lisa Hugo" in line for line in lines)


def test_an_empty_wall_clears_everyone():
    leads = [normalize.map_row({"Name": f"Person {i}", "Website": f"s{i}.ae"})
             for i in range(5)]
    assert len(dedupe.partition(leads, dedupe.ContactWall())["clear"]) == 5


# ------------------------------------------------------- the wall on disk


def test_the_repo_wall_loads():
    """`data/contacted-before.csv` is read on every batch. If it stops loading,
    the machine's most consequential check silently stops working."""
    wall = dedupe.ContactWall.from_csv()
    assert len(wall) > 100, f"only {len(wall)} contacts"


def test_the_repo_wall_still_carries_its_warm_threads():
    wall = dedupe.ContactWall.from_csv()
    warm = [c for c in wall.by_name.values() if c.warm]
    assert len(warm) == 9, [c.name for c in warm]


def test_a_known_warm_lead_is_matched_from_the_repo_wall():
    wall = dedupe.ContactWall.from_csv()
    hit = dedupe.check_early(normalize.map_row({"Name": "Lisa Hugo"}), wall)
    assert hit and hit.warm


def test_a_missing_wall_file_yields_an_empty_wall_not_a_crash():
    """The CLI turns this into a hard failure rather than a silent pass — a
    missing file must never read as "nobody has been contacted"."""
    wall = dedupe.ContactWall.from_csv("/nonexistent/wall.csv")
    assert len(wall) == 0


def test_warm_reads_every_spelling_a_human_might_type():
    for value in ("yes", "Yes", "TRUE", "1", "y"):
        assert dedupe._truthy(value), value
    for value in ("no", "", "false", None, "0"):
        assert not dedupe._truthy(value), value


def test_rows_round_trip_through_to_rows():
    wall = dedupe.ContactWall.from_csv()
    rows = wall.to_rows()
    assert len(rows) == len(wall)
    assert set(rows[0]) == {"name", "email", "domain", "warm", "status", "track"}
    # Warm first, so a human scanning the file sees the dangerous ones at the top.
    assert rows[0]["warm"] == "yes"


def test_a_csv_wall_and_a_records_wall_agree():
    """The CRM-export path and the CSV path must produce the same verdicts, or
    a one-off export would quietly disagree with the committed wall."""
    from_csv = dedupe.ContactWall.from_csv()
    from_records = dedupe.ContactWall.from_records([
        {"name": r["name"], "email": r["email"], "domain": r["domain"],
         "warm": r["warm"], "status": r["status"]}
        for r in from_csv.to_rows()
    ])
    lead = normalize.map_row({"Name": "Lisa Hugo"})
    a = dedupe.check_early(lead, from_csv)
    b = dedupe.check_early(lead, from_records)
    assert bool(a) == bool(b) and a.warm == b.warm


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


def test_a_profile_handle_that_is_not_the_lead_gets_a_note():
    """The cheapest half of the ownership check, and it costs no request at
    all. A note, never a drop: plenty of real people have a handle that is a
    brand or a nickname."""
    lead = normalize.map_row({"Name": "Sarah Khan",
                              "LinkedIn": "https://linkedin.com/in/mikeoconnor"})
    assert any("does not contain this lead's name" in n for n in lead.notes)


def test_a_matching_handle_gets_no_note():
    lead = normalize.map_row({"Name": "Sarah Khan",
                              "LinkedIn": "https://linkedin.com/in/sarahkhan"})
    assert not any("does not contain" in n for n in lead.notes)


def test_a_handle_with_digits_still_matches():
    lead = normalize.map_row({"Name": "Sarah Khan",
                              "LinkedIn": "https://linkedin.com/in/sarah-khan-8a41b2"})
    assert not any("does not contain" in n for n in lead.notes)


def test_no_name_means_no_ownership_note():
    lead = normalize.map_row({"LinkedIn": "https://linkedin.com/in/whoever"})
    assert not any("does not contain" in n for n in lead.notes)
