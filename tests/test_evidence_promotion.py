"""Tests for evidence promotion (audit/evidence_promotion.py) — the
append-only bridge from ephemeral evidence/<slug>/ scratch to the permanent,
committed docs/leads/<slug>/evidence/ folder.

Hermetic: runs entirely against a tmp_path cwd, never touches the repo's
real evidence/ or docs/leads/ directories.

Run: python -m pytest tests/test_evidence_promotion.py -q
     (or plain `python tests/test_evidence_promotion.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import evidence_promotion as ep

try:
    from PIL import Image
    _HAVE_PIL = True
except ImportError:
    _HAVE_PIL = False

import pytest

pytestmark = pytest.mark.skipif(not _HAVE_PIL, reason="Pillow not installed")


def _make_source(base: "os.PathLike", slug: str, rel: str, size=(2400, 1800)) -> None:
    path = os.path.join(str(base), "evidence", slug, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.new("RGB", size, color=(80, 120, 200)).save(path)


def test_promote_resizes_and_strips_metadata(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_source(tmp_path, "jane-doe", "screenshots/foo.png")

    result = ep.promote("jane-doe", "finding", "screenshots/foo.png", rank=1)

    dest = tmp_path / "docs" / "leads" / "jane-doe" / "evidence" / "finding-1.png"
    assert dest.is_file()
    assert result["repo_path"] == str(dest.relative_to(tmp_path))
    assert result["github_url"] == (
        "https://github.com/haytham10/Funnel-Auditor/blob/uae-track/"
        "docs/leads/jane-doe/evidence/finding-1.png"
    )
    with Image.open(dest) as im:
        assert max(im.size) <= ep.MAX_EDGE
        assert im.info == {}


def test_promote_hook_kind_ignores_rank(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_source(tmp_path, "jane-doe", "hook/1.png")

    ep.promote("jane-doe", "hook", "hook/1.png")

    assert (tmp_path / "docs" / "leads" / "jane-doe" / "evidence" / "hook.png").is_file()


def test_promote_finding_without_rank_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_source(tmp_path, "jane-doe", "screenshots/foo.png")

    with pytest.raises(ep.PromotionError):
        ep.promote("jane-doe", "finding", "screenshots/foo.png")


def test_promote_missing_source_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ep.PromotionError):
        ep.promote("jane-doe", "finding", "screenshots/nope.png", rank=1)


def test_promote_refuses_overwrite_without_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_source(tmp_path, "jane-doe", "screenshots/foo.png")
    ep.promote("jane-doe", "finding", "screenshots/foo.png", rank=1)

    with pytest.raises(ep.PromotionError):
        ep.promote("jane-doe", "finding", "screenshots/foo.png", rank=1)


def test_promote_force_overwrites(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_source(tmp_path, "jane-doe", "screenshots/foo.png")
    ep.promote("jane-doe", "finding", "screenshots/foo.png", rank=1)

    # Should not raise.
    ep.promote("jane-doe", "finding", "screenshots/foo.png", rank=1, force=True)


def test_promote_bad_kind_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_source(tmp_path, "jane-doe", "screenshots/foo.png")

    with pytest.raises(ep.PromotionError):
        ep.promote("jane-doe", "bogus", "screenshots/foo.png", rank=1)


def test_print_promote_exit_codes(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _make_source(tmp_path, "jane-doe", "screenshots/foo.png")

    assert ep.print_promote("jane-doe", "finding", "screenshots/foo.png", rank=1) == 0
    assert ep.print_promote("jane-doe", "finding", "screenshots/foo.png", rank=1) == 1
    out = capsys.readouterr().out
    assert "PROMOTE EVIDENCE: OK" in out
    assert "PROMOTE EVIDENCE: FAIL" in out


if __name__ == "__main__":
    print("This suite uses pytest fixtures (tmp_path/monkeypatch/capsys) — "
          "run with `python -m pytest tests/test_evidence_promotion.py -q`.")
    sys.exit(0)
