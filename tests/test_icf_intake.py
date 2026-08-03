"""An ICF directory export, read as Leads and as the ICP fields it answers.

Run: python -m pytest tests/test_icf_intake.py -q
 or: python tests/test_icf_intake.py

Three failures this file exists to make impossible.

**The hyperlink.** `ICF profile` reads the literal string "View profile" in all
311 rows and the URL lives only in `cell.hyperlink.target`. A CSV conversion
produces a fully-populated column carrying nothing, and it looks fine. So the
fixture workbook here sets real hyperlinks — the bug is not reproducible without
them.

**`Personal and Organizational`.** 79 of the 92 populated `Client type` cells
say it, and it means the coach ticked both boxes. `qualify.classify_sells_to`
already rules that a source saying both says nothing. Mapping it either way puts
a wrong identity line in front of 79 people.

**The relabelled number.** `Rate (listed)` is a USD hourly band and
`top_program_price_aed` is an AED program price. `main.py lint` fails closed on
a relabelled number and this is the one place in this change that could quietly
create one.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))
os.environ.setdefault("OUTBOUND_COPY_SOURCE", "csv")

import openpyxl                                               # noqa: E402

from outbound import icf_intake                               # noqa: E402

HEADERS = ["Name", "Credential", "Email", "Phone (E.164)", "Phone status",
           "Website", "City", "Emirate", "Rate (listed)", "Fee range",
           "Coaching themes", "Client type", "Languages",
           "Profile completeness %", "ICF profile", "Name (as listed)",
           "Location (raw)", "ICF key"]

ROW = {
    "Name": "Cindy Van De Kreke",
    "Credential": "MCC",
    "Email": "cindyvandekreke@live.com",
    "Phone (E.164)": "+971501566210",
    "Phone status": "ok",
    "Website": "http://www.cindyvandekreke.com",
    "City": "Dubai",
    "Emirate": "Dubai",
    "Rate (listed)": "$500-999 per hour",
    "Fee range": "$500-999 per hour",
    "Coaching themes": "Organizational Leadership Development | Team Effectiveness",
    "Client type": "Personal and Organizational",
    "Languages": "Dutch | English",
    "Profile completeness %": "1",
    "ICF profile": "View profile",
    "Name (as listed)": "Mrs. Cindy Van De Kreke, MCC",
    "Location (raw)": "Dubai, UNITED ARAB EMIRATES",
    "ICF key": "85BC1CDD-BCB7-46DE-8332-8F2F0DA52642",
}

PROFILE_URL = ("https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx"
               "?webcode=ccfcoachprofileview&coachcstkey=85BC1CDD")


def _workbook(path, rows=(ROW,), *, sheet=icf_intake.SHEET, links=True) -> str:
    """A workbook shaped like the real export, hyperlinks and all."""
    book = openpyxl.Workbook()
    grid = book.active
    grid.title = sheet
    grid.append(HEADERS)
    for offset, row in enumerate(rows, start=2):
        grid.append([row.get(h, "") for h in HEADERS])
        if not links:
            continue
        for header, target in (("Email", "mailto:" + row.get("Email", "")),
                               ("Website", row.get("Website", "") + "/"),
                               ("ICF profile", PROFILE_URL)):
            if not row.get(header):
                continue
            cell = grid.cell(offset, HEADERS.index(header) + 1)
            cell.hyperlink = target
    book.save(path)
    return str(path)


# ------------------------------------------------------------- the hyperlink


def test_icf_profile_url_comes_from_the_hyperlink_not_the_text(tmp_path):
    """The column reads "View profile" in every row. The URL is the target."""
    records = icf_intake.load_sheet(_workbook(tmp_path / "icf.xlsx"))
    assert records[0]["ICF profile"] == "View profile"
    assert records[0]["_icf_profile_url"] == PROFILE_URL


def test_mailto_is_unwrapped(tmp_path):
    records = icf_intake.load_sheet(_workbook(tmp_path / "icf.xlsx"))
    assert records[0]["_email_url"] == "cindyvandekreke@live.com"


def test_cell_text_is_used_when_it_is_itself_a_url(tmp_path):
    """A row with no hyperlink still has a website, read off the text."""
    records = icf_intake.load_sheet(
        _workbook(tmp_path / "icf.xlsx", links=False))
    assert records[0]["_website_url"] == "http://www.cindyvandekreke.com"
    # And "View profile" is not a URL, so it produces nothing rather than
    # a string that looks like one.
    assert records[0]["_icf_profile_url"] == ""


# ------------------------------------------------------- the sells_to mapping


def test_personal_and_organizational_says_nothing():
    """79 of the 92 populated rows. Both boxes ticked is not an answer."""
    out = icf_intake.prefill(dict(ROW, **{"Client type": "Personal and Organizational"}))
    assert out["sells_to"] == ""
    assert "says both" in out["sells_to_source"]


def test_the_two_unambiguous_client_types_map():
    assert icf_intake.prefill(dict(ROW, **{"Client type": "Personal Only"}))["sells_to"] \
        == "individuals"
    assert icf_intake.prefill(dict(ROW, **{"Client type": "Organizational Only"}))["sells_to"] \
        == "corporates"


def test_a_blank_client_type_is_distinguishable_from_a_contradictory_one():
    """Both produce "", and an empty field with no reason attached cannot tell
    "nobody filled it in" from "they ticked both"."""
    blank = icf_intake.prefill(dict(ROW, **{"Client type": ""}))
    both = icf_intake.prefill(dict(ROW, **{"Client type": "Personal and Organizational"}))
    assert blank["sells_to"] == both["sells_to"] == ""
    assert blank["sells_to_source"] != both["sells_to_source"]
    assert "blank" in blank["sells_to_source"]


# --------------------------------------------------------- the number nobody
#                                                            gets to relabel


def test_the_hourly_band_never_becomes_a_program_price():
    out = icf_intake.prefill(ROW)
    assert out["hourly_rate_usd_band"] == "$500-999 per hour"
    assert "top_program_price_aed" not in out


# ------------------------------------------------------------------- the lead


def test_the_icf_profile_url_is_never_the_lead_site(tmp_path):
    """It is a directory listing on coachingfederation.org. In `site_url` it
    would point tier-0 fetch at ICF's own page for every lead on the list."""
    leads, _ = icf_intake.ingest(_workbook(tmp_path / "icf.xlsx"))
    lead = leads[0]
    assert "coachingfederation" not in lead.site_url
    assert not any("coachingfederation" in u for u in lead.other_urls)
    assert lead.site_url == "https://cindyvandekreke.com"


def test_a_linkedin_url_in_the_website_column_becomes_a_channel(tmp_path):
    """Nine real rows do this, and it is a LinkedIn nobody has to search for."""
    row = dict(ROW, Website="https://www.linkedin.com/in/dana-zaarour/",
               Name="Dana Zaarour")
    leads, _ = icf_intake.ingest(_workbook(tmp_path / "icf.xlsx", [row]))
    assert leads[0].linkedin_url == "https://linkedin.com/in/dana-zaarour"
    assert leads[0].site_url == ""


def test_a_foreign_phone_becomes_a_note_never_a_drop(tmp_path):
    row = dict(ROW, **{"Phone status": "foreign"})
    leads, _ = icf_intake.ingest(_workbook(tmp_path / "icf.xlsx", [row]))
    assert any("non-UAE" in n for n in leads[0].notes)
    assert leads[0].name == "Cindy Van De Kreke"


def test_country_is_set_because_the_export_is_one_country(tmp_path):
    leads, _ = icf_intake.ingest(_workbook(tmp_path / "icf.xlsx"))
    assert leads[0].country == "United Arab Emirates"


def test_prefill_is_keyed_on_the_one_lead_key(tmp_path):
    from outbound.fetch import lead_key

    leads, prefills = icf_intake.ingest(_workbook(tmp_path / "icf.xlsx"))
    assert set(prefills) == {lead_key(leads[0])}


def test_every_prefilled_value_says_it_came_from_a_directory():
    out = icf_intake.prefill(ROW)
    assert out["source"] == icf_intake.PROVENANCE
    assert out["coach_type_source"].startswith(icf_intake.PROVENANCE)


def test_solo_is_never_inferred():
    """Nothing on the sheet says it, so nothing here may claim it."""
    assert "solo" not in icf_intake.prefill(ROW)


# --------------------------------------------------------------- failing shut


def test_a_missing_sheet_is_an_error_not_an_empty_list(tmp_path):
    path = _workbook(tmp_path / "icf.xlsx", sheet="Sheet1")
    try:
        icf_intake.load_sheet(path)
    except icf_intake.ICFIntakeError as exc:
        assert "Coaches" in str(exc)
    else:
        raise AssertionError("a missing sheet must never read as zero coaches")


def test_an_unreadable_workbook_is_an_error(tmp_path):
    path = tmp_path / "not-a-workbook.xlsx"
    path.write_text("this is not a zip archive", encoding="utf-8")
    try:
        icf_intake.load_sheet(str(path))
    except icf_intake.ICFIntakeError:
        pass
    else:
        raise AssertionError("a file that cannot be opened must fail closed")


def test_unmapped_columns_are_reported(tmp_path):
    """Silence here is expensive — `intake`'s own lesson, where an unmapped
    website column skipped the whole free site-read tier without a word."""
    unmapped = icf_intake.unmapped_columns(_workbook(tmp_path / "icf.xlsx"))
    assert "Coaching themes" in unmapped
    assert "ICF key" in unmapped
    assert "Name" not in unmapped
    assert "Email" not in unmapped


def test_report_names_the_free_mail_share(tmp_path):
    """69% of the real list, and `email-enrich` has no path on any of them."""
    leads, prefills = icf_intake.ingest(_workbook(tmp_path / "icf.xlsx"))
    text = icf_intake.report(leads, prefills)
    assert "free-mail" in text
    assert "1 lead(s)" in text


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
