"""
Vision-pass completeness gate.

The root problem this exists to fix: the skill's Step 1.5 says "Read every
downloaded image," and a session can genuinely report "4 screenshots read"
in its final verdict while a transcript audit shows only 1 of those 4 ever
had a Read tool call against it. Free-text self-report has no way to catch
that gap — the model believes its own summary. A manifest file with an
explicit mark-per-file requirement does, because "vision pass complete"
becomes a computed fact (every required path has read=true) instead of a
sentence someone typed.

This module has NO opinion on what's in an image. It only tracks which
required image files have been explicitly marked read during this session,
and it refuses to say the pass is complete until every one of them has.

Manifest file: evidence/<slug>/vision_manifest.json

    {
      "slug": "lynsey-ward",
      "generated": "2026-07-10T11:08:16",
      "images": [
        {"path": "ig/1.png", "category": "ig_screenshot",
         "required": true, "read": false, "read_at": null},
        ...
      ]
    }

Requirement rules (mirror process-lead Step 1.5 / opener-finder Step B,
word for word — if those change, update REQUIRED_MOBILE_TYPES to match):
- every file under ig/ and hook/           -> required (all of Haytham's
  pasted evidence — legacy IG sourcing screenshots and UAE-track hook
  evidence alike; there's no "skim the evidence" tier)
- every crawled page's screenshot_desktop  -> required
- a page's screenshot_mobile               -> required only when the page's
  link_type is the bio page or an offer/checkout/booking page — this is the
  literal scope the skill asks for ("mobile screenshot of the bio page and
  of every offer/checkout/booking page"), not "every mobile screenshot"
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REQUIRED_MOBILE_TYPES = {"bio_page", "sales", "course", "checkout", "booking"}
IMAGE_EXTS = (".png", ".jpg", ".jpeg")
MANIFEST_NAME = "vision_manifest.json"


@dataclass
class ImageRecord:
    path: str          # relative to the evidence dir, e.g. "ig/1.png"
    category: str       # ig_screenshot | hook_evidence | site_desktop | site_mobile
    required: bool
    read: bool = False
    read_at: str | None = None

    def as_dict(self) -> dict:
        return {
            "path": self.path, "category": self.category,
            "required": self.required, "read": self.read, "read_at": self.read_at,
        }


def _manifest_path(evidence_dir: Path) -> Path:
    return evidence_dir / MANIFEST_NAME


def _load(evidence_dir: Path) -> dict:
    p = _manifest_path(evidence_dir)
    if not p.exists():
        return {"slug": evidence_dir.name, "generated": None, "images": []}
    return json.loads(p.read_text())


def _save(evidence_dir: Path, data: dict) -> None:
    _manifest_path(evidence_dir).write_text(json.dumps(data, indent=2))


def _scan_ig_images(evidence_dir: Path) -> list[ImageRecord]:
    """Pasted-evidence folders: ig/ (legacy parenting-track sourcing
    screenshots) and hook/ (UAE-track hook evidence Haytham pastes —
    LinkedIn posts, podcast pages, About screenshots). Every file in
    either folder is required — there's no "skim the evidence" tier."""
    records: list[ImageRecord] = []
    for folder, category in (("ig", "ig_screenshot"), ("hook", "hook_evidence")):
        d = evidence_dir / folder
        if not d.is_dir():
            continue
        records.extend(
            ImageRecord(path=f"{folder}/{f.name}", category=category, required=True)
            for f in sorted(d.iterdir())
            if f.suffix.lower() in IMAGE_EXTS
        )
    return records


def _rel(evidence_dir: Path, path_str: str) -> str:
    """evidence.json stores screenshot paths as given to the crawler, which
    may be relative-to-evidence-dir already or may carry the evidence dir's
    own name as a prefix — normalize either shape to "screenshots/foo.png"."""
    p = Path(path_str)
    try:
        return str(p.relative_to(evidence_dir))
    except ValueError:
        parts = p.parts
        if evidence_dir.name in parts:
            idx = parts.index(evidence_dir.name)
            return str(Path(*parts[idx + 1:]))
        return str(p)


def _scan_site_images(evidence_dir: Path) -> list[ImageRecord]:
    ev_path = evidence_dir / "evidence.json"
    if not ev_path.exists():
        return []
    ev = json.loads(ev_path.read_text())
    out: list[ImageRecord] = []
    for p in ev.get("pages", []):
        if p.get("error"):
            continue  # a page that failed to load never produced a screenshot
        desktop = p.get("screenshot_desktop")
        mobile = p.get("screenshot_mobile")
        if desktop:
            out.append(ImageRecord(path=_rel(evidence_dir, desktop),
                                    category="site_desktop", required=True))
        if mobile:
            out.append(ImageRecord(
                path=_rel(evidence_dir, mobile), category="site_mobile",
                required=p.get("link_type") in REQUIRED_MOBILE_TYPES,
            ))
    return out


def init_manifest(evidence_dir: Path) -> dict:
    """(Re)build the manifest from whatever is on disk right now. Safe to
    call more than once in either order — IG screenshots usually land
    before the crawl runs (skill Step 0), site screenshots after (Step 1);
    calling this again after either one just adds the new files without
    resetting read=true on ones already confirmed."""
    existing = _load(evidence_dir)
    prior = {r["path"]: r for r in existing.get("images", [])}

    by_path: dict[str, ImageRecord] = {}
    for rec in _scan_ig_images(evidence_dir) + _scan_site_images(evidence_dir):
        if rec.path in by_path:
            by_path[rec.path].required = by_path[rec.path].required or rec.required
        else:
            by_path[rec.path] = rec

    for path, rec in by_path.items():
        old = prior.get(path)
        if old and old.get("read"):
            rec.read, rec.read_at = True, old.get("read_at")

    data = {
        "slug": evidence_dir.name,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "images": [r.as_dict() for r in sorted(by_path.values(), key=lambda r: r.path)],
    }
    _save(evidence_dir, data)
    return data


def mark_read(evidence_dir: Path, *paths: str) -> tuple[list[str], list[str]]:
    """Mark one or more paths as read. Returns (marked, unknown).

    An unrecognized path is reported back, never silently accepted — the
    whole point is that a typo'd or wrong path must not count as coverage.
    Run `vision list` to see the exact expected paths if one gets rejected.
    """
    data = _load(evidence_dir)
    by_path = {r["path"]: r for r in data.get("images", [])}
    marked, unknown = [], []
    now = datetime.now().isoformat(timespec="seconds")
    for raw in paths:
        key = raw.lstrip("/")
        if key not in by_path:
            unknown.append(raw)
            continue
        by_path[key]["read"] = True
        by_path[key]["read_at"] = now
        marked.append(raw)
    _save(evidence_dir, data)
    return marked, unknown


def check(evidence_dir: Path) -> tuple[bool, dict]:
    """(complete, summary). complete is True only when every required image
    has read=true. This is the one function anything downstream (the
    opener-finder's lane call, the final report) is allowed to treat as
    ground truth for "vision pass done.\""""
    data = _load(evidence_dir)
    images = data.get("images", [])
    required = [r for r in images if r["required"]]
    unread = [r for r in required if not r["read"]]
    return (len(unread) == 0), {
        "total_required": len(required),
        "total_read": len(required) - len(unread),
        "unread": unread,
    }


def format_check_line(evidence_dir: Path) -> str:
    """The exact one-line string the skills are required to quote verbatim
    in their final report / Notion Evidence section — never paraphrased as
    'N screenshots read.' Complete and incomplete cases are worded
    differently on purpose so a truncated paste can't be misread as the
    other."""
    complete, s = check(evidence_dir)
    if complete:
        return f"VISION PASS: COMPLETE — {s['total_read']} of {s['total_required']} required images confirmed read"
    return (f"VISION PASS: INCOMPLETE — {s['total_read']} of {s['total_required']} required images "
            f"confirmed read, {len(s['unread'])} unread")


def is_read(evidence_dir: Path, path: str) -> bool:
    """Used by the SMYKM-hook guard: before a hook citing specific IG post
    content can be used, the image it came from must show read=true here."""
    data = _load(evidence_dir)
    for r in data.get("images", []):
        if r["path"] == path.lstrip("/"):
            return bool(r["read"])
    return False


def print_check(evidence_dir: Path) -> int:
    complete, summary = check(evidence_dir)
    print(format_check_line(evidence_dir))
    if not complete:
        print("Unread:")
        for r in summary["unread"]:
            print(f"  [{r['category']}] {r['path']}")
    return 0 if complete else 1


def print_list(evidence_dir: Path) -> int:
    data = _load(evidence_dir)
    if not data.get("images"):
        print(f"No manifest / no images found for {evidence_dir}. "
              f"Run `python main.py vision init {evidence_dir}` first.")
        return 1
    for r in data["images"]:
        status = "read" if r["read"] else ("REQUIRED-UNREAD" if r["required"] else "optional-unread")
        print(f"{status:<18} [{r['category']}] {r['path']}")
    return 0
