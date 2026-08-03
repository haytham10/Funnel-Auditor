"""What the CLI does when it is handed something wrong.

Every gate in this machine is quoted verbatim by a skill rather than
paraphrased, which only works if a bad input produces a readable line and a
meaningful exit code. A traceback does neither: it reads as "the run crashed"
when the truth is "the wall could not be checked" or "a worker returned a list
where the schema says object", and an orchestrator that cannot tell those apart
either stops a good batch or, worse, waves a bad one through.

The contract these tests pin:

    exit 0   the check ran and passed
    exit 1   the check ran and something failed (a warm hit, a lint failure)
    exit 2   the check could NOT run

Exit 2 is the one that matters. A missing wall file must never read as "nobody
has been contacted".
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def offline_env() -> dict:
    """The CLI's environment with the Airtable key removed.

    `doc-check` runs its CRM schema check whenever a key is present, which is
    the right default for a person and the wrong one for a suite: the tests
    would reach the network on a developer machine and not in CI, so a failure
    would depend on who ran them. Same reason conftest.py pins
    OUTBOUND_COPY_SOURCE=csv. The schema check has its own tests, against a stub.
    """
    env = dict(os.environ)
    env.pop("AIRTABLE_API_KEY", None)
    return env


def run(*args, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT, input=stdin, capture_output=True, text=True, env=offline_env(),
    )


def write(tmp: str, name: str, payload) -> str:
    path = Path(tmp) / name
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload),
                    encoding="utf-8")
    return str(path)


# --------------------------------------------------------------- the wall


def test_a_missing_wall_file_exits_2_not_a_traceback():
    """The most consequential failure in the machine. A wall that cannot be
    read must stop the batch, and must say so in a line a skill can quote."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        result = run("dedupe", leads, "--contacts", f"{tmp}/does-not-exist.csv")
        assert result.returncode == 2, result.stdout + result.stderr
        assert "Traceback" not in result.stderr
        assert "cannot read the wall" in result.stdout


def test_a_corrupt_wall_file_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        bad = write(tmp, "wall.json", "{not json at all")
        result = run("dedupe", leads, "--contacts", bad)
        assert result.returncode == 2, result.stdout + result.stderr
        assert "Traceback" not in result.stderr


def test_an_empty_wall_exits_2_rather_than_clearing_everyone():
    """"The file parsed and held nothing" and "nobody has ever been contacted"
    are the same bytes and opposite meanings."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        empty = write(tmp, "wall.json", [])
        result = run("dedupe", leads, "--contacts", empty)
        assert result.returncode == 2, result.stdout + result.stderr
        assert "the wall is empty" in result.stdout


# ------------------------------------------------- one object, not a list


def test_qualify_on_a_json_array_exits_2_with_a_readable_line():
    """A worker returning a list where the schema says object used to raise
    AttributeError, which reads as a crash rather than the schema violation it
    is."""
    result = run("qualify", "-", stdin=json.dumps([{"name": "Sarah"}]))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "one JSON object" in result.stdout


def test_research_accepts_a_slice_array():
    """`research-worker` handles a slice of about ten leads and returns an
    array. This used to exit 2 with "expected one JSON object, got list",
    printed beside a skill instruction that says a schema violation goes back
    to the worker once — so the documented validation step failed on the
    documented file, in a way that read like the worker returned garbage."""
    slice_of_two = [
        {"name": "A", "uae_based": "yes", "is_coach": "yes", "active_recent": "unclear"},
        {"name": "B", "uae_based": "yes", "is_coach": "yes", "active_recent": "unclear"},
    ]
    result = run("research", "-", stdin=json.dumps(slice_of_two))
    assert "Traceback" not in result.stderr
    assert "RESEARCH A" in result.stdout and "RESEARCH B" in result.stdout
    assert "2 valid" in result.stdout or "/2" in result.stdout


def test_research_still_takes_a_single_object():
    result = run("research", "-", stdin=json.dumps(
        {"name": "A", "uae_based": "yes", "is_coach": "yes", "active_recent": "unclear"}))
    assert "Traceback" not in result.stderr
    assert "RESEARCH A" in result.stdout


def test_an_empty_research_slice_exits_2():
    """A worker that returned nothing is not a slice that passed."""
    result = run("research", "-", stdin="[]")
    assert result.returncode == 2, result.stdout
    assert "returned nothing" in result.stdout


def test_a_missing_input_file_exits_2():
    result = run("qualify", "/nope/not/here.json")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "cannot read" in result.stdout


def test_malformed_json_exits_2():
    result = run("qualify", "-", stdin="{oh dear")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr


# ------------------------------------------------------------ the warm stop


def test_a_warm_hit_exits_1():
    """Not 2. The check ran fine; what it found is the problem, and the two
    cases need different handling by the caller."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Rita Baki"}])
        wall = write(tmp, "wall.json", [
            {"Contact Name": "Rita Baki", "Status": "Reply Received"},
            {"Contact Name": "Someone Else", "Status": "Outreach Sent"},
        ])
        result = run("dedupe", leads, "--contacts", wall)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "WARM THREAD" in result.stdout


def test_a_clean_batch_exits_0():
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        wall = write(tmp, "wall.json", [
            {"Contact Name": "Rita Baki", "Status": "Reply Received"},
        ])
        result = run("dedupe", leads, "--contacts", wall)
        assert result.returncode == 0, result.stdout + result.stderr


# ------------------------------------------------ every command, every bad file


BAD_INPUT_CASES = [
    ("lint",       "bad.json"),
    ("deal",       "bad.json"),
    ("export",     "bad.json"),
    ("dedupe",     "bad.json"),
    ("qualify",    "bad.json"),
    ("research",   "bad.json"),
    ("copy-sync",  "bad.json"),
]


def test_no_command_tracebacks_on_malformed_json():
    """A JSONDecodeError traceback reads as "the run crashed" when the truth is
    "that file is not JSON", and a skill quoting a gate cannot tell them apart."""
    with tempfile.TemporaryDirectory() as tmp:
        bad = write(tmp, "bad.json", "{not json at all")
        for command, _ in BAD_INPUT_CASES:
            args = [command, bad]
            if command == "export":
                args += ["--out", str(Path(tmp) / "out")]
            result = run(*args)
            assert "Traceback" not in result.stderr, f"{command}: {result.stderr[-300:]}"
            assert result.returncode == 2, f"{command} exited {result.returncode}"


def test_no_command_tracebacks_on_a_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        for command in ("lint", "deal", "dedupe", "qualify", "research",
                        "copy-sync", "intake", "wall-add", "copy-usage"):
            args = [command, "/nope/does-not-exist.json"]
            result = run(*args)
            assert "Traceback" not in result.stderr, f"{command}: {result.stderr[-300:]}"
            assert result.returncode == 2, f"{command} exited {result.returncode}"


def test_a_json_object_where_an_array_belongs_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        obj = write(tmp, "obj.json", {"a": 1})
        for command in ("deal", "dedupe"):
            result = run(command, obj)
            assert result.returncode == 2, f"{command} exited {result.returncode}"
            assert "Traceback" not in result.stderr


def test_an_empty_batch_does_not_crash_the_deal_report():
    """`next(iter(...))` on an empty share table raised StopIteration, which is
    a traceback on a command whose whole output is meant to be quotable."""
    with tempfile.TemporaryDirectory() as tmp:
        empty = write(tmp, "empty.json", [])
        # `--allow-cached-copy` because `run` strips the key: an offline deal
        # now refuses rather than silently drawing from the committed cache.
        result = run("deal", empty, "--allow-cached-copy")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Traceback" not in result.stderr
        assert "0 leads" in result.stdout


def test_deal_refuses_to_draw_from_the_cache_without_being_told_to():
    """Airtable owns the lines. Falling back to `copy/*.csv` is legitimate and
    must never be silent: an unreadable table means nothing just checked that
    the cache is current, and a whole batch of subtly stale copy is the failure
    this is here to make impossible."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json",
                      [{"email": "a@x.ae", "coach_type": "Health",
                        "sells_to": "individuals"}])
        result = run("deal", leads)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "NOT live" in result.stdout
        assert "--allow-cached-copy" in result.stdout
        assert "Traceback" not in result.stderr


def test_copy_check_without_a_key_is_exit_2_and_says_so():
    """A check that cannot run is a failure, never a pass."""
    result = run("copy-check")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "COPY-CHECK: BLOCKED" in result.stdout
    assert "Traceback" not in result.stderr


def test_wall_add_refuses_a_file_with_the_wrong_columns():
    """It printed "0 added, 104 -> 104", which reads exactly like "this batch
    was already walled". Those leads would never enter the wall and would be
    contacted a second time — the failure the wall exists to prevent, reached
    through a mistyped path."""
    with tempfile.TemporaryDirectory() as tmp:
        wrong = write(tmp, "wrong.csv", "alpha,beta\n1,2\n")
        result = run("wall-add", wrong)
        assert result.returncode == 2, result.stdout
        assert "none of the expected columns" in result.stdout
        assert "0 added" not in result.stdout


def test_copy_usage_refuses_a_file_with_the_wrong_columns():
    with tempfile.TemporaryDirectory() as tmp:
        wrong = write(tmp, "wrong.csv", "alpha,beta\n1,2\n")
        result = run("copy-usage", wrong)
        assert result.returncode == 2, result.stdout
        assert "none of the expected columns" in result.stdout


def test_piping_a_gate_into_head_does_not_traceback():
    """Piping a gate's output into head or grep is ordinary, and the default
    BrokenPipeError handling prints a traceback on exit — which looks exactly
    like a crash in a command whose job is to be believed."""
    import subprocess
    proc = subprocess.run(
        f"{sys.executable} main.py facts 2>&1 | head -2",
        cwd=ROOT, shell=True, capture_output=True, text=True)
    assert "Traceback" not in proc.stdout + proc.stderr
    assert "BrokenPipe" not in proc.stdout + proc.stderr


def test_qualify_settles_activity_from_the_page_when_no_date_is_given():
    """The bridge existed only as a library function and the CLI never reached
    it, so all twelve leads on the first real batch came back `unclear` on
    activity — the floor doing nothing at all."""
    with tempfile.TemporaryDirectory() as tmp:
        lead = write(tmp, "lead.json", {
            "name": "Test Coach", "city": "Dubai", "domain": "x.ae",
            "headline": "Life Coach",
            "site_text": "Coaching in Dubai. Latest article 2026-07-20 on pricing.",
        })
        result = run("qualify", lead)
        assert "activity settled from" in result.stdout, result.stdout
        assert "2026-07-20" in result.stdout


def test_qualify_prefers_a_date_the_worker_supplied():
    with tempfile.TemporaryDirectory() as tmp:
        lead = write(tmp, "lead.json", {
            "name": "Test Coach", "city": "Dubai", "headline": "Life Coach",
            "last_activity": "2026-07-25",
            "site_text": "Latest article 2020-01-01.",
        })
        result = run("qualify", lead)
        assert "2026-07-25" in result.stdout
        assert "activity settled from" not in result.stdout


def _days_ago(n: int) -> str:
    from datetime import date, timedelta
    return (date.today() - timedelta(days=n)).isoformat()


def test_qualify_settles_activity_from_a_fresh_observation():
    """F3, end to end. The dated evidence this floor never had has existed
    since P1; nothing read it until now."""
    with tempfile.TemporaryDirectory() as tmp:
        lead = write(tmp, "lead.json", {
            "name": "Test Coach", "city": "Dubai", "headline": "Life Coach",
            "site_text": "I help leaders find their edge. Book a call.",
            "observations": [{"url": "https://linkedin.com/posts/abc",
                              "published_at": _days_ago(4)}],
        })
        result = run("qualify", lead)
        assert result.returncode == 0, result.stdout
        assert "linkedin.com/posts/abc" in result.stdout, result.stdout
        assert "active in 30 days" in result.stdout


def test_a_stale_observation_set_qualifies_exactly_like_no_observations():
    """**The safety property, checked through the CLI and not only the
    library.** A lead whose retrieved pages are all old must come back the same
    as a lead with nothing retrieved. Otherwise giving this floor better
    evidence has quietly given it a kill it was built not to have."""
    payload = {"name": "Test Coach", "city": "Dubai", "headline": "Life Coach",
               "site_text": "I help leaders find their edge. Book a call."}
    with tempfile.TemporaryDirectory() as tmp:
        bare = run("qualify", write(tmp, "bare.json", dict(payload)))
        stale = run("qualify", write(tmp, "stale.json", dict(
            payload, observations=[{"url": "https://linkedin.com/posts/abc",
                                    "published_at": _days_ago(200)}])))
    assert stale.returncode == bare.returncode == 0, stale.stdout
    assert "active in 30 days: UNCLEAR" in stale.stdout, stale.stdout
    # The verdict lines are identical; only the provenance note differs, and it
    # says what it saw rather than pretending it saw nothing.
    verdicts = lambda out: [l for l in out.splitlines() if ":" in l and "settled" not in l]
    assert verdicts(stale.stdout) == verdicts(bare.stdout)
    assert "too old to settle the floor, and never a kill" in stale.stdout


def test_observe_unwraps_a_research_file():
    """The batch skill has always said to run this on a research file, and until
    a real batch did, nobody noticed a research object is not an observation:
    ten fine objects produced fifty violations about missing platforms and urls.
    `research` was checking the nested list correctly all along — the documented
    way to LOOK at it was what was broken."""
    obs = {"lead_key": "a@x.ae", "platform": "linkedin", "url": "https://li/p/1",
           "fetched_at": "2026-08-01T09:00:00", "published_at": "2026-07-30",
           "author": "self", "kind": "post", "text": "a real post",
           "retrieved_by": "apify:li_posts"}
    with tempfile.TemporaryDirectory() as tmp:
        research = write(tmp, "r.json", [
            {"name": "A", "email": "a@x.ae", "observations": [obs]},
            {"name": "B", "email": "b@x.ae", "observations": [dict(obs, lead_key="b@x.ae")]},
        ])
        result = run("observe", research)
    assert result.returncode == 0, result.stdout
    assert "unwrapped 2 observation(s) from 2 research object(s)" in result.stdout
    assert "VALID" in result.stdout


def test_observe_still_takes_bare_observations():
    """The two shapes are both legitimate inputs, and which one it is is a
    question the file already answers."""
    obs = {"lead_key": "a@x.ae", "platform": "site", "url": "https://x.ae",
           "fetched_at": "2026-08-01T09:00:00", "author": "self",
           "kind": "bio", "text": "coach", "retrieved_by": "tier0"}
    with tempfile.TemporaryDirectory() as tmp:
        result = run("observe", write(tmp, "o.json", [obs]))
    assert result.returncode == 0, result.stdout
    assert "unwrapped" not in result.stdout


def test_metrics_exits_2_on_a_ledger_it_could_not_read():
    """A batch whose cost could not be computed must not report as a batch that
    cost nothing — the wall's asymmetry, two stages over."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "b.json", [{"lead_key": "a@x.ae", "hook": "x",
                                       "hook_verified": "verified"}])
        result = run("metrics", leads, "--batch", "no-such-batch-at-all")
    assert result.returncode == 2, result.stdout
    assert "not a zero-cost batch" in result.stdout
    assert "Traceback" not in result.stderr


def test_metrics_never_fails_a_batch_over_a_number():
    """It is an observer. A gate that can halt a send file over an accounting
    line is a gate people learn to route around."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "b.json", [{"lead_key": "a@x.ae", "hook": "",
                                       "hook_verified": "none"}])
        result = run("metrics", leads, "--no-ledger", "--out",
                     str(Path(tmp) / "m.json"))
    assert result.returncode == 0, result.stdout
    assert "null_hook_rate    100%" in result.stdout
    # Nothing was supplied, so nothing may print as a zero.
    assert "Raw Count        ?" in result.stdout
    assert "Apify Cost USD   ?" in result.stdout


def test_replies_exits_2_naming_the_headers_rather_than_reporting_no_replies():
    """A zero reply rate from a column it failed to find would read as "the
    campaign did nothing" when the truth is "the question could not be asked"."""
    with tempfile.TemporaryDirectory() as tmp:
        export = write(tmp, "e.csv", "prospect,outcome_code\na@x.ae,7\n")
        leads = write(tmp, "l.json", [{"email": "a@x.ae", "hook_type": "WORK"}])
        result = run("replies", export, "--leads", leads)
    assert result.returncode == 2, result.stdout
    assert "prospect" in result.stdout and "outcome_code" in result.stdout
    assert "--email-column" in result.stdout


def test_replies_refuses_to_guess_a_prefiltered_export():
    """A pre-filtered file and an unrecognised reply column look identical and
    differ by the whole answer."""
    with tempfile.TemporaryDirectory() as tmp:
        export = write(tmp, "e.csv", "email,first_name\na@x.ae,Amina\n")
        leads = write(tmp, "l.json", [{"email": "a@x.ae", "hook_type": "WORK"}])
        result = run("replies", export, "--leads", leads)
        assert result.returncode == 2, result.stdout
        assert "--all-replied" in result.stdout

        ok = run("replies", export, "--leads", leads, "--all-replied")
        assert ok.returncode == 0, ok.stdout
        assert "NOT A VERDICT" in ok.stdout


def test_a_malformed_last_activity_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        lead = write(tmp, "lead.json", {
            "name": "X", "last_activity": "not-a-date", "site_text": "coach in dubai"})
        result = run("qualify", lead)
        assert result.returncode == 2, result.stdout
        assert "Traceback" not in result.stderr
        assert "ISO date" in result.stdout


def test_lint_assembles_the_body_from_beats():
    """A drafting worker's whole contract is beats, and `lint` answered "body is
    empty" — so the PASS line the worker is required to quote was unobtainable.
    Telling workers to assemble their own is worse: the order is load-bearing,
    and a worker that joined it differently would quote a PASS about text that
    is not what ships, with word count the check most likely to differ."""
    draft = {
        "slug": "sarah-ahmed", "name": "Sarah Ahmed",
        "subject": "your hashimoto post",
        "beats": {
            "hook": ("You wrote that you couldn't contain the excitement of "
                     "uncovering a solution for yourself."),
            "identity": ("My job is finding your next client. A health coach in "
                         "Dubai closed AED 78,000 over 2 months from prospects "
                         "I put in front of them."),
            "offer": ("I pulled 10 names for you before writing this. Not a "
                      "scraped list, people I'd actually start with."),
            "cta": ("15 minutes and they're yours the same day. I'll tell you "
                    "why these 10 and not the other 40."),
            "ps": "ps: a no here costs you nothing and costs me nothing.",
        },
    }
    result = run("lint", "-", stdin=json.dumps([draft]))
    assert result.returncode == 0, result.stdout
    assert "PASS" in result.stdout
    assert "body is empty" not in result.stdout


def test_lint_uses_an_explicit_body_when_one_is_given():
    """The assembler is a fallback, not an override."""
    result = run("lint", "-", stdin=json.dumps([{
        "name": "X", "subject": "a subject", "body": "", "beats": {}}]))
    assert "body is empty" in result.stdout


def test_the_same_assembler_serves_lint_and_export():
    """One assembler, used by both commands, is the only version that cannot
    drift. If these ever diverge, a draft lints clean and ships different text."""
    import subprocess
    check = subprocess.run(
        [sys.executable, "-c",
         "import main, outbound.export as e, inspect;"
         "src = inspect.getsource(main.cmd_lint);"
         "print('assemble_body' in src and 'from outbound.export import' in src)"],
        cwd=ROOT, capture_output=True, text=True)
    assert check.stdout.strip() == "True", check.stdout + check.stderr


# ------------------------------------------------------------------- observe


def test_observe_rejects_an_observation_naming_an_actor_that_does_not_exist():
    """A record of a fetch that did not happen reads exactly like a real one to
    everything downstream. Exit 1: the check ran and something failed."""
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "obs.json", [{
            "lead_key": "a@b.com", "platform": "linkedin", "url": "https://x/1",
            "fetched_at": "2026-08-01T09:00:00", "author": "self", "kind": "post",
            "text": "a real sentence", "retrieved_by": "apify:not_an_actor"}])
        out = run("observe", path)
        assert out.returncode == 1, out.stdout
        assert "not an actor this machine has" in out.stdout


def test_observe_exits_2_on_something_that_is_not_an_object():
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "obs.json", "a string")
        out = run("observe", path)
        assert out.returncode == 2, out.stdout
        assert "OBSERVE: FAIL" in out.stdout


# ------------------------------------------------------------------- resolve


def test_resolve_exits_0_when_every_channel_names_somebody_else():
    """R3 of the hook-retrieval proposal, in code. Ownership gates *spend*,
    never inclusion — a false kill is permanent and invisible, and exit 1 on an
    `absent` verdict is the natural mistake that would make one."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = [{"name": "Sarah Khan", "email": "sarah@x.ae",
                  "slug": "sarah-khan",
                  "instagram_url": "https://instagram.com/themindsetlab"}]
        path = write(tmp, "leads.json", json.dumps(leads))
        out = run("resolve", path)
        assert out.returncode == 0, out.stdout
        assert "RESOLVE:" in out.stdout and "Advisory" in out.stdout


def test_resolve_exits_2_when_the_sites_file_is_not_what_fetch_writes():
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", json.dumps([{"name": "A", "email": "a@x.ae"}]))
        sites = write(tmp, "sites.json", json.dumps({"sites": "not an object"}))
        out = run("resolve", leads, "--sites", sites)
        assert out.returncode == 2, out.stdout
        assert "RESOLVE: FAIL" in out.stdout


# ---------------------------------------------------------------------- plan


def test_plan_exits_0_when_every_paid_rung_is_declined():
    """D21 in code, one stage after `resolve` pins the same rule — and the half
    that survives D27 turning the gate on. A decline is about a purchase and
    never about a lead, so exit 1 here would turn an ownership verdict into the
    inclusion gate the decision forbids, whether or not the decline binds."""
    with tempfile.TemporaryDirectory() as tmp:
        identities = {"identities": [{
            "lead_key": "rory@x.ae", "name": "Rory Buck",
            "owner_verdict": "absent",
            "channels": [{"platform": "linkedin",
                          "url": "https://linkedin.com/in/harrisonassessments",
                          "handle": "harrisonassessments", "confidence": "absent",
                          "evidence": "handle contains no part of their name",
                          "source": "site"}]}]}
        path = write(tmp, "identity.json", json.dumps(identities))
        out = run("plan", path)
        assert out.returncode == 0, out.stdout
        # Two, because LinkedIn is two rungs: a profile scrape and a posts
        # scrape are different actors at different prices, and an ownership
        # verdict that refuses the channel refuses both purchases.
        assert "declined 2 paid step(s)" in out.stdout
        assert "never inclusion" in out.stdout


def test_plan_does_not_price_a_paid_rung_unless_asked():
    """Pricing needs a token and the network, and this helper does not strip
    APIFY_TOKEN — so a default-on lookup would reach Apify on a developer
    machine and not in CI, which is the failure `offline_env` exists to stop.
    An unpriced batch must never report as a free one."""
    with tempfile.TemporaryDirectory() as tmp:
        identities = {"identities": [{
            "lead_key": "a@x.ae", "name": "A Coach",
            "channels": [{"platform": "linkedin",
                          "url": "https://linkedin.com/in/acoach",
                          "handle": "acoach", "confidence": "confirmed",
                          "evidence": "handle 'acoach' contains 'coach'",
                          "source": "row"}]}]}
        path = write(tmp, "identity.json", json.dumps(identities))
        out = run("plan", path)
        assert out.returncode == 0, out.stdout
        assert "NO ESTIMATE" in out.stdout
        assert "$0.0000" not in out.stdout


def test_plan_exits_2_when_the_identity_file_is_not_what_resolve_writes():
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "identity.json", "a string")
        out = run("plan", path)
        assert out.returncode == 2, out.stdout
        assert "PLAN: FAIL" in out.stdout


# -------------------------------------------------------------------- select


def test_select_exits_0_when_it_would_pick_nothing():
    """No hook found is a good answer. The lead holds; it does not fail."""
    with tempfile.TemporaryDirectory() as tmp:
        rows = [{"name": "A", "email": "a@x.ae", "observations": [{
            "lead_key": "a@x.ae", "platform": "web", "url": "https://news/1",
            "fetched_at": "2026-08-01T09:00:00", "published_at": "2026-07-20",
            "author": "third_party", "kind": "post",
            "text": "Gulf News profiles the coach helping women return to work.",
            "retrieved_by": "websearch"}]}]
        path = write(tmp, "researched.json", json.dumps(rows))
        out = run("select", path)
        assert out.returncode == 0, out.stdout
        assert "third_party" in out.stdout


def test_select_disagreeing_with_a_verified_hook_is_never_a_failure():
    """A measurement that can fail a batch is a measurement people route
    around — the ledger's own rule, one stage over."""
    with tempfile.TemporaryDirectory() as tmp:
        rows = [{"name": "A", "email": "a@x.ae", "hook_verified": "verified",
                 "hook_source_url": "https://linkedin.com/posts/never-fetched",
                 "observations": []}]
        path = write(tmp, "researched.json", json.dumps(rows))
        out = run("select", path, "--against")
        assert out.returncode == 0, out.stdout
        assert "AGAINST:" in out.stdout


def test_select_never_calls_a_stored_quote_verified():
    """R2. The verifier's live re-fetch is the only thing that has ever caught
    a fabricated claim, and a report that reads as verification retires it.

    More load-bearing since the flip, not less: the quote a hook cites now comes
    out of text a different agent stored hours earlier, so the live fetch is the
    only check that the stored text was ever real."""
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "researched.json", json.dumps([{"email": "a@x.ae"}]))
        out = run("select", path)
        assert out.returncode == 0, out.stdout
        assert "STORED" in out.stdout
        assert "re-fetch" in out.stdout


def test_select_exits_2_on_something_that_is_not_a_research_object():
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "researched.json", json.dumps(["a string"]))
        out = run("select", path)
        assert out.returncode == 2, out.stdout
        assert "SELECT: FAIL" in out.stdout


# ----------------------------------------------------------- escalate-only


def test_escalate_only_refuses_a_file_that_is_not_a_sites_json():
    """It takes `fetch --out`'s payload, not a Leads file. Handing it the wrong
    one must name the difference rather than reporting nothing to escalate,
    which is what "no plans" would look like."""
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "leads.json", [{"name": "A"}])
        result = run("fetch", path, "--escalate-only")
        assert result.returncode == 2, result.stdout
        assert "escalate_plans" in result.stdout


def test_escalate_only_reads_nothing_at_tier_0():
    """The retry path, and the reason it exists. `--escalate` after a failed
    escalation re-reads every site first: 52 duplicate `(lead, url)` pairs went
    into the ledger of the one batch whose purpose was a duplicate count.

    Asserted against the ledger, because "it did not fetch" is the claim."""
    with tempfile.TemporaryDirectory() as tmp:
        env = offline_env()
        env["OUTBOUND_LEDGER_ROOT"] = tmp
        sites = write(tmp, "sites.json", {
            "tier0_rate": 0.5, "sites": {},
            "escalate_plans": [{"actor_key": "site_render", "urls": ["https://a.ae"],
                                "why": "1 url(s) returned 200 with no text"}]})
        result = subprocess.run(
            [sys.executable, "main.py", "fetch", sites, "--escalate-only"],
            cwd=ROOT, capture_output=True, text=True, env=env)
        assert result.returncode == 0, result.stdout
        assert "ESCALATE" in result.stdout
        # Unapproved, so nothing was bought — and nothing was read either.
        assert not (Path(tmp) / "data" / "runs").exists(), \
            "a run that fetched nothing must leave no retrieval lines"


def test_escalate_only_does_not_buy_a_plan_that_already_ran():
    """A retry is for the half that failed.

    On `2026-08-02-q3` the render plan died three times and the static plan
    beside it succeeded every time, so each retry bought the same 12 pages
    again. The free tier-0 re-read was only the version of this duplicate that
    got caught first; the paid one is worse and was never checked for.
    """
    with tempfile.TemporaryDirectory() as tmp:
        sites = write(tmp, "sites.json", {
            "tier0_rate": 0.5, "sites": {},
            "escalate_plans": [
                {"actor_key": "site_static", "urls": ["https://a.ae"],
                 "why": "1 url(s) unreachable"},
                {"actor_key": "site_render", "urls": ["https://b.ae"],
                 "why": "1 url(s) returned 200 with no text"}],
            "escalated": {"site_static": [{"url": "https://a.ae", "text": "x"}]}})
        result = run("fetch", sites, "--escalate-only")
        assert result.returncode == 0, result.stdout
        assert "SKIP" in result.stdout and "site_static" in result.stdout
        # The one that has not run is still offered.
        assert "ESCALATE" in result.stdout


def test_escalate_only_when_every_plan_has_already_run():
    """Nothing left to retry is a success, not an empty purchase."""
    with tempfile.TemporaryDirectory() as tmp:
        sites = write(tmp, "sites.json", {
            "tier0_rate": 0.5, "sites": {},
            "escalate_plans": [{"actor_key": "site_static",
                                "urls": ["https://a.ae"], "why": "1 url(s)"}],
            "escalated": {"site_static": [{"url": "https://a.ae"}]}})
        result = run("fetch", sites, "--escalate-only", "--approve-cost")
        assert result.returncode == 0, result.stdout
        assert "already run" in result.stdout


def test_escalate_only_with_no_plans_is_not_an_error():
    """A batch whose tier 0 read everything has nothing to retry, and that is a
    success rather than a missing file."""
    with tempfile.TemporaryDirectory() as tmp:
        sites = write(tmp, "sites.json",
                      {"tier0_rate": 1.0, "sites": {}, "escalate_plans": []})
        result = run("fetch", sites, "--escalate-only")
        assert result.returncode == 0, result.stdout
        assert "nothing to escalate" in result.stdout


# -------------------------------------------------------------------- ledger


def test_a_missing_ledger_exits_2_not_a_zero_cost_report():
    """The wall's asymmetry, one stage over. A batch whose ledger is not there
    must not report as a batch that spent nothing — that is the one reading
    that would make the number worth less than no number."""
    with tempfile.TemporaryDirectory() as tmp:
        env = offline_env()
        env["OUTBOUND_LEDGER_ROOT"] = tmp
        out = subprocess.run(
            [sys.executable, "main.py", "ledger", "report", "--batch", "never-ran"],
            cwd=ROOT, capture_output=True, text=True, env=env)
        assert out.returncode == 2, out.stdout
        assert "LEDGER: FAIL" in out.stdout


def test_a_duplicate_fetch_is_reported_without_failing():
    """Reporting one is the job. Failing on one belongs to the stage that
    removes it — a gate that can halt a send file over an accounting line is a
    gate people learn to route around."""
    with tempfile.TemporaryDirectory() as tmp:
        env = offline_env()
        env["OUTBOUND_LEDGER_ROOT"] = tmp

        def ledger(*args):
            return subprocess.run([sys.executable, "main.py", "ledger", *args],
                                  cwd=ROOT, capture_output=True, text=True, env=env)

        for stage in ("research", "hook"):
            added = ledger("add", "--batch", "b", "--lead", "a@b.com", "--stage", stage,
                           "--url", "https://linkedin.com/in/x", "--by", "webfetch")
            assert added.returncode == 0, added.stdout

        out = ledger("report", "--batch", "b")
        assert out.returncode == 0, out.stdout
        assert "DUPLICATE" in out.stdout


# ------------------------------------------------------------------ doc-check


def test_doc_check_passes_on_the_real_repo():
    result = run("doc-check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DOC-CHECK: PASS" in result.stdout


def test_doc_check_exits_2_when_it_cannot_read_the_docs():
    """A missing docs tree must never read as "no drift", for exactly the
    reason a missing wall must never read as "nobody has been contacted"."""
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("main.py", "outbound", "audit", "copy", "CLAUDE.md",
                     ".gitignore"):
            src = ROOT / name
            dst = Path(tmp) / name
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, dst)
        (Path(tmp) / "docs").mkdir()
        result = subprocess.run([sys.executable, "main.py", "doc-check"],
                                cwd=tmp, capture_output=True, text=True,
                                env=offline_env())
        assert result.returncode == 2, result.stdout + result.stderr
        assert "Traceback" not in result.stdout + result.stderr
        assert "could not run" in result.stdout
        assert "docs/spec" in result.stdout, "it must name what it could not read"


def test_piping_doc_check_into_head_does_not_traceback():
    """doc-check prints one line per finding plus a summary, so it is the
    command most likely to be piped into head or grep."""
    proc = subprocess.run(
        f"{sys.executable} main.py doc-check 2>&1 | head -1",
        cwd=ROOT, shell=True, capture_output=True, text=True, env=offline_env())
    assert "Traceback" not in proc.stdout + proc.stderr
    assert "BrokenPipe" not in proc.stdout + proc.stderr


# ------------------------------------------------------------ channel-find
#
# The first command here that spends on a whole list at once, so its
# preconditions are the ones worth pinning.


def test_channel_find_without_a_readable_leads_file_exits_2():
    """Not exit 1. A gate that could not establish its precondition could not
    run, and the precondition here is that the wall has been checked."""
    with tempfile.TemporaryDirectory() as tmp:
        proc = run("channel-find", "--leads", str(Path(tmp) / "nope.json"))
    assert proc.returncode == 2, proc.stdout
    assert "dedupe" in proc.stdout


def test_channel_find_refuses_a_json_object_where_the_clear_list_belongs():
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "leads.json", {"leads": []})
        proc = run("channel-find", "--leads", path)
    assert proc.returncode == 2, proc.stdout


def test_channel_find_without_execute_spends_nothing_and_writes_nothing():
    """`fetch --escalate`'s rule. The plan prints, including the real query
    strings, and no state file appears."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json",
                      [{"name": "Sarah Khan", "city": "Dubai",
                        "email": "sarah@khan.ae"}])
        state = str(Path(tmp) / "state.json")
        proc = run("channel-find", "--leads", leads, "--state", state)
        assert proc.returncode == 0, proc.stdout
        assert "PLAN ONLY" in proc.stdout
        assert '"Sarah Khan" Dubai coach' in proc.stdout
        assert not Path(state).exists(), "a plan must not write a state file"


def test_channel_find_resumes_on_membership_not_a_counter():
    """A chunk that died halfway leaves the leads it answered for. The next
    invocation owes exactly the remainder."""
    with tempfile.TemporaryDirectory() as tmp:
        from outbound.fetch import lead_key
        from outbound.normalize import Lead

        done = Lead(name="Sarah Khan", city="Dubai", email="sarah@khan.ae")
        leads = write(tmp, "leads.json",
                      [done.to_dict(),
                       Lead(name="Dana Zaarour", city="Dubai",
                            email="dana@z.ae").to_dict()])
        state = write(tmp, "state.json",
                      {"batch": "t", "shape": "one", "chunks": [],
                       "leads": {lead_key(done): {"name": "Sarah Khan",
                                                  "verdict": "FOUND"}}})
        proc = run("channel-find", "--leads", leads, "--state", state)
    assert proc.returncode == 0, proc.stdout
    assert "1 lead(s)" in proc.stdout
    assert "Dana Zaarour" in proc.stdout
    assert "Sarah Khan" not in proc.stdout


def test_channel_find_says_so_when_every_lead_is_already_done():
    with tempfile.TemporaryDirectory() as tmp:
        from outbound.fetch import lead_key
        from outbound.normalize import Lead

        done = Lead(name="Sarah Khan", city="Dubai", email="sarah@khan.ae")
        leads = write(tmp, "leads.json", [done.to_dict()])
        state = write(tmp, "state.json",
                      {"batch": "t", "shape": "one", "chunks": [],
                       "leads": {lead_key(done): {"name": "Sarah Khan",
                                                  "verdict": "FOUND"}}})
        proc = run("channel-find", "--leads", leads, "--state", state)
    assert proc.returncode == 0, proc.stdout
    assert "nothing to search" in proc.stdout


def test_icf_intake_on_a_missing_sheet_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        import openpyxl

        path = Path(tmp) / "book.xlsx"
        book = openpyxl.Workbook()
        book.active.title = "NotCoaches"
        book.save(path)
        proc = run("icf-intake", str(path))
    assert proc.returncode == 2, proc.stdout
    assert "Coaches" in proc.stdout


def test_icf_intake_on_a_file_that_is_not_a_workbook_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, "book.xlsx", "definitely not a zip archive")
        proc = run("icf-intake", path)
    assert proc.returncode == 2, proc.stdout
    assert "Traceback" not in proc.stdout + proc.stderr


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
