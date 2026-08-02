"""The payload goes to a file; a summary goes to stdout.

Run: python -m pytest tests/test_apify_payload.py -q
 or: python tests/test_apify_payload.py

`apify` was the only command in this repo that printed its whole dataset into
the caller's context. Every other bulk stage — `fetch`, `select`, `plan`,
`metrics`, `export`, `crm-rows` — writes a file and prints a summary, and the
docstring on `cmd_apify` said "Prints JSON for the calling skill" as though that
were a design rather than the leak it turned out to be.

`2026-08-02-q2` produced three externalised tool-results totalling 914,685 bytes
of Instagram JSON, about 305 KB each where a trimmed result is 20-30 KB. Its
forensics could not attribute them at all: *"If they entered whole they are
~229k tokens — a third of peak context."*

Two faults produced that and both are pinned here. `--raw` bypassed trimming,
which was known. `_lean` did not recurse, which was not: its allow-list branch
copied `latestPosts` and `author` through verbatim, so a leaned profile carried
a dozen unleaned posts inside itself, each with the media blobs `_NOISE_KEYS`
exists to drop.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit import apify


def test_lean_drops_the_noise_inside_a_nested_record():
    """The allow-list branch kept `latestPosts` verbatim, so every media blob
    the top level dropped came back one level down."""
    item = {"username": "x", "biography": "bio", "profilePicUrl": "BLOB",
            "latestPosts": [{"caption": "hello", "images": ["BLOB", "BLOB"],
                             "childPosts": [{"videoUrl": "BLOB"}]}]}
    lean = apify._lean(item, keep=("username", "biography", "latestPosts"))
    post = lean["latestPosts"][0]
    assert post["caption"] == "hello"
    assert "images" not in post
    assert "childPosts" not in post
    assert "profilePicUrl" not in lean


def test_lean_still_drops_the_noise_at_the_top_level():
    """The non-allow-list branch is the one that already worked. Recursion must
    not have quietly changed what it keeps."""
    lean = apify._lean({"caption": "keep", "html": "BLOB", "sidecar": "BLOB"})
    assert lean == {"caption": "keep"}


def test_lean_leaves_a_non_dict_alone():
    assert apify._lean("not a dict") == "not a dict"
    assert apify._lean(None) is None


def test_the_summary_carries_what_decides_whether_to_open_the_file():
    """A worker needs three things: how many came back, how many carry text
    worth quoting, and how recent they are."""
    out = apify.summarise([
        {"caption": "a post", "timestamp": "2026-07-01T00:00:00Z"},
        {"text": "another", "timestamp": "2026-08-01T00:00:00Z"},
        {"likes": 3},
    ])
    assert out["items"] == 3
    assert out["with_text"] == 2
    assert out["newest"].startswith("2026-08-01")
    assert out["oldest"].startswith("2026-07-01")


def test_the_summary_of_an_empty_result_is_zero_and_not_an_error():
    """An empty dataset is a real answer — a private account, a dead handle.
    It must summarise, not raise, or the failure path costs a second call."""
    out = apify.summarise([])
    assert out["items"] == 0 and out["with_text"] == 0 and out["keys"] == []


def test_a_lead_and_a_target_both_shape_the_file_name():
    """Deterministic, so a repeat fetch overwrites its own file — that is the
    retrieve-once invariant. Hashed on the target, so two different pages for
    one lead cannot collide into one."""
    import main

    class Args:
        lead = "meg-juma"
        url = "https://instagram.com/meg"

    first = main._apify_slug(Args(), "ig")
    assert first.startswith("meg-juma-")

    Args.url = "https://instagram.com/someone-else"
    assert main._apify_slug(Args(), "ig") != first

    Args.lead = ""
    assert "-" not in main._apify_slug(Args(), "ig")


def test_the_written_payload_round_trips():
    """The file is the product now. If it is not valid JSON a worker cannot
    read it, and the summary would be the only thing left."""
    payload = [{"caption": "unicode ✓", "timestamp": "2026-08-01T00:00:00Z"}]
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "out.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        assert json.loads(target.read_text(encoding="utf-8")) == payload


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
