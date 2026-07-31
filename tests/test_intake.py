"""Intake and dedupe: the two cheap stages that run before anything is spent.

Run: python -m pytest tests/test_intake.py -q
 or: python tests/test_intake.py

The dedupe tests carry the highest stakes in the repo. A cold opener landing on
a live warm thread is the only failure here that destroys something rather than
wasting something, and it has already happened twice.
"""

import sys
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


def test_a_bare_platform_root_is_junk():
    """instagram.com with no handle tells us nothing about anyone."""
    assert normalize.classify_site("https://instagram.com").verdict == "junk"


def test_a_parked_domain_is_parked():
    assert normalize.classify_site("http://hugedomains.com/x").verdict == "parked"


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
