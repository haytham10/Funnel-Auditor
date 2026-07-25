"""
Evidence promotion — the append-only bridge from ephemeral working evidence
to the permanent, committed record.

Every screenshot a walk produces lives only under `evidence/<slug>/`
(gitignored, scratch — gone the moment a cloud container is reclaimed).
Nothing there survives past a session unless it is explicitly promoted
here, to `docs/leads/<slug>/evidence/`, which the repo's `.gitignore`
carves out as the one committed exception (`!docs/leads/**/*.png`).

Promotion is deliberately lossy in file size, not in proof: full-page PNGs
run 0.5-3MB, and committing ~313 of them unoptimized (150-900MB) is Git-LFS
territory. Resized to a 1600px longest edge and stripped of metadata they
land at 150-400KB, so the whole promoted set stays well inside plain git.

It is one-way and append-only by design — `--force` is required to
overwrite an existing promoted file, because a silent overwrite destroys
the only surviving proof of an earlier finding.
"""

from __future__ import annotations

from pathlib import Path

from config import EVIDENCE_DIR

REPO = "haytham10/Funnel-Auditor"
BRANCH = "uae-track"

MAX_EDGE = 1600
LEADS_DIR = Path("docs/leads")


class PromotionError(Exception):
    """Raised on any problem that should stop promotion before it writes
    anything — missing source, an existing dest without --force, or a
    bad --kind. Callers print this and exit non-zero."""


def _dest_filename(kind: str, rank: int | None) -> str:
    if kind == "finding":
        if rank is None:
            raise PromotionError("--kind finding requires --rank N")
        return f"finding-{rank}.png"
    if kind == "hook":
        return "hook.png"
    raise PromotionError(f"unknown --kind {kind!r} — must be 'finding' or 'hook'")


def promote(slug: str, kind: str, source: str, rank: int | None = None,
            force: bool = False) -> dict:
    """Resize + strip + compress `source` (resolved relative to
    evidence/<slug>/) and write it to docs/leads/<slug>/evidence/<dest>.png.

    Returns {"repo_path", "github_url", "size_kb"}. Raises PromotionError
    without writing anything on a missing source, an existing dest (unless
    force), or a bad kind. Imports Pillow lazily so `crm-gate`/`send-cap`
    keep working on a machine that never installed it."""
    from PIL import Image

    src_path = Path(EVIDENCE_DIR) / slug / source
    if not src_path.is_file():
        raise PromotionError(f"source not found: {src_path}")

    dest_name = _dest_filename(kind, rank)
    dest_dir = LEADS_DIR / slug / "evidence"
    dest_path = dest_dir / dest_name

    if dest_path.exists() and not force:
        raise PromotionError(
            f"{dest_path} already exists — evidence is append-only, pass --force to overwrite"
        )

    dest_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(src_path) as im:
        im.load()
        im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        im.info = {}  # drop exif/icc/text metadata chunks
        if im.mode not in ("RGB", "RGBA", "P", "L", "LA"):
            im = im.convert("RGB")
        im.save(dest_path, format="PNG", optimize=True)

    size_kb = dest_path.stat().st_size / 1024
    return {
        "repo_path": str(dest_path),
        "github_url": f"https://github.com/{REPO}/blob/{BRANCH}/{dest_path.as_posix()}",
        "size_kb": round(size_kb, 1),
    }


def print_promote(slug: str, kind: str, source: str, rank: int | None = None,
                   force: bool = False) -> int:
    """CLI-facing wrapper: prints the result line, returns the exit code."""
    try:
        result = promote(slug, kind, source, rank=rank, force=force)
    except PromotionError as exc:
        print(f"PROMOTE EVIDENCE: FAIL — {exc}")
        return 1
    print(f"PROMOTE EVIDENCE: OK — {result['repo_path']} ({result['size_kb']} KB)")
    print(result["github_url"])
    return 0
