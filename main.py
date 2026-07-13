"""
Funnel Auditor — CLI entry point.

Usage:
    python main.py walk <url> [--name NAME] [--handle @H] [--followers N] [--out DIR]
    python main.py crawl <url>          # crawl + summary only, no evidence packet
    python main.py <url>                # same as walk

`walk` produces the full evidence packet (evidence.json + packet.md + page
text + screenshots) under ./evidence/<slug>/ — the machine half of the
5-stop funnel walk, ready to hand to the opener-finder skill. It drives a
real Playwright/Chromium browser and is the fallback fetch path.

The primary fetch path (Firecrawl, driven by the calling skill rather than
this CLI) uses four narrower commands instead of `walk`, so the scope,
priority, and analysis logic stay in one place regardless of which layer
did the fetching:

    python main.py discover-links <html-file> <url> [--platform NAME]
    python main.py discover-checkout <html-file> <url>
    python main.py screenshot-name <url> <suffix>
    python main.py ingest <manifest.json> [--name] [--handle] [--followers] [--out DIR]

See `.claude/skills/process-lead/SKILL.md` Step 1 for the orchestration
that calls these, and the module docstrings in `audit/crawler.py` /
`audit/evidence.py` for what each wraps.
"""

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from config import EVIDENCE_DIR
from audit.crawler import (
    crawl, CrawlResult, CrawledPage,
    detect_platform, extract_links, extract_checkout_links, _safe_filename,
)
from audit.urls import slugify
from audit import vision_gate

console = Console()


def print_summary(result: CrawlResult) -> None:
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]Funnel Auditor[/bold cyan]  •  [dim]{result.seed_url}[/dim]",
            border_style="cyan",
        )
    )
    console.print(
        f"[bold]Platform detected:[/bold] [yellow]{result.platform.upper()}[/yellow]\n"
    )

    # --- Funnel path table ---
    if result.pages:
        path_table = Table(
            "Depth", "Type", "URL", "Title", "Load (ms)", "Desktop SS", "Mobile SS", "Error",
            box=box.ROUNDED,
            title="[bold green]Funnel Path[/bold green]",
            show_lines=True,
        )
        for p in result.pages:
            error_text = Text(p.error[:60] + "…" if len(p.error) > 60 else p.error, style="red") if p.error else Text("—", style="dim")
            path_table.add_row(
                str(p.depth),
                f"[cyan]{p.link_type}[/cyan]",
                p.url[:60] + ("…" if len(p.url) > 60 else ""),
                p.title[:40] + ("…" if len(p.title) > 40 else "") if p.title else "[dim]—[/dim]",
                f"{p.load_time_ms:.0f}" if p.load_time_ms else "[dim]—[/dim]",
                "✓" if p.screenshot_desktop else "[red]✗[/red]",
                "✓" if p.screenshot_mobile else "[red]✗[/red]",
                error_text,
            )
        console.print(path_table)

    # --- Funnel links found ---
    if result.funnel_links:
        console.print()
        fl_table = Table(
            "Category", "Label", "URL",
            box=box.SIMPLE,
            title="[bold yellow]Funnel-Relevant Links Found[/bold yellow]",
        )
        for lnk in result.funnel_links:
            fl_table.add_row(
                f"[green]{lnk['category']}[/green]",
                lnk["label"][:40] or "[dim]—[/dim]",
                lnk["url"][:70] + ("…" if len(lnk["url"]) > 70 else ""),
            )
        console.print(fl_table)

    # --- Noise links ---
    if result.noise_links:
        console.print()
        nl_table = Table(
            "Label", "URL",
            box=box.SIMPLE,
            title=f"[dim]Noise Links Skipped ({len(result.noise_links)})[/dim]",
        )
        for lnk in result.noise_links:
            nl_table.add_row(
                lnk["label"][:40] or "[dim]—[/dim]",
                lnk["url"][:70] + ("…" if len(lnk["url"]) > 70 else ""),
            )
        console.print(nl_table)

    console.print()
    console.print(f"[bold]Pages crawled:[/bold] {len(result.pages)}")
    console.print()


def _normalize_url(url: str) -> str:
    url = url.strip()
    return url if url.startswith("http") else "https://" + url


def cmd_walk(args: argparse.Namespace) -> None:
    from audit.evidence import build_evidence

    url = _normalize_url(args.url)
    slug = slugify(args.name or args.handle or url)
    out_dir = Path(args.out) if args.out else Path(EVIDENCE_DIR) / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold cyan]Walking funnel:[/bold cyan] {url}")
    console.print(f"[dim]Evidence packet → {out_dir}[/dim]\n")

    with console.status("[bold green]Crawling funnel…[/bold green]", spinner="dots"):
        result = crawl(url, screenshot_dir=str(out_dir / "screenshots"))

    print_summary(result)

    with console.status("[bold green]Building evidence packet…[/bold green]", spinner="dots"):
        packet_dir = build_evidence(
            result,
            out_dir,
            lead_name=args.name or "",
            handle=args.handle or "",
            followers=args.followers,
        )

    console.print(Panel.fit(
        f"[bold green]Evidence packet ready[/bold green]\n"
        f"[bold]{packet_dir / 'packet.md'}[/bold]\n"
        f"{packet_dir / 'evidence.json'}",
        border_style="green",
    ))
    console.print()


def cmd_crawl(args: argparse.Namespace) -> None:
    url = _normalize_url(args.url)
    console.print(f"\n[bold cyan]Starting crawl:[/bold cyan] {url}\n")
    with console.status("[bold green]Crawling funnel…[/bold green]", spinner="dots"):
        result = crawl(url)
    print_summary(result)


def cmd_slug(args: argparse.Namespace) -> None:
    print(slugify(args.value))


def cmd_discover_links(args: argparse.Namespace) -> None:
    """Wraps extract_links() + detect_platform() for a page whose HTML was
    fetched by something other than this process (Firecrawl, driven by a
    skill). Prints JSON so the caller can decide what to fetch next —
    scope/priority rules stay defined here, once, regardless of fetcher."""
    html = Path(args.html_file).read_text()
    url = _normalize_url(args.url)
    platform = args.platform or detect_platform(url)
    funnel_links, noise_links, external_refs = extract_links(html, url, platform)
    print(json.dumps({
        "platform": platform,
        "funnel_links": funnel_links,
        "noise_links": noise_links,
        "external_refs": external_refs,
    }, indent=2))


def cmd_discover_checkout(args: argparse.Namespace) -> None:
    """Wraps extract_checkout_links() — the Stop 4 checkout-hop discovery,
    same scope rules as discover-links, for a page fetched elsewhere."""
    html = Path(args.html_file).read_text()
    url = _normalize_url(args.url)
    print(json.dumps(extract_checkout_links(html, url), indent=2))


def cmd_screenshot_name(args: argparse.Namespace) -> None:
    """Prints the exact filename crawl() would have used for this URL +
    suffix (desktop/mobile), so a screenshot fetched by something other
    than Playwright lands under evidence/<slug>/screenshots/ with a name
    the packet renderer and vision-gate path matching already expect."""
    print(f"{_safe_filename(_normalize_url(args.url))}_{args.suffix}.png")


def _page_from_manifest(entry: dict, manifest_dir: Path) -> CrawledPage:
    html = ""
    html_file = entry.get("html_file")
    if html_file:
        html = (manifest_dir / html_file).read_text()
    return CrawledPage(
        url=entry["url"],
        title=entry.get("title", ""),
        link_type=entry["link_type"],
        load_time_ms=entry.get("load_time_ms", 0.0),
        screenshot_desktop=entry.get("screenshot_desktop", ""),
        screenshot_mobile=entry.get("screenshot_mobile", ""),
        depth=entry.get("depth", 0),
        source_url=entry.get("source_url", ""),
        error=entry.get("error", ""),
        http_status=entry.get("http_status", 0),
        external=entry.get("external", False),
        html=html,
        cta_clicks=entry.get("cta_clicks", []),
    )


def cmd_ingest(args: argparse.Namespace) -> None:
    """Reads a manifest JSON describing pages fetched by something other
    than this process's own crawl() (Firecrawl, driven by a skill),
    reconstructs a CrawlResult exactly as crawl() would have produced, and
    runs it through the UNCHANGED build_evidence() — identical output
    contract to `main.py walk`, regardless of which layer did the fetch."""
    from audit.evidence import build_evidence

    manifest_path = Path(args.manifest)
    manifest_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text())

    pages = [_page_from_manifest(p, manifest_dir) for p in manifest["pages"]]
    result = CrawlResult(
        seed_url=manifest["seed_url"],
        platform=manifest.get("platform", "direct"),
        pages=pages,
        funnel_links=manifest.get("funnel_links", []),
        noise_links=manifest.get("noise_links", []),
        external_refs=manifest.get("external_refs", []),
    )

    slug = slugify(args.name or args.handle or result.seed_url)
    out_dir = Path(args.out) if args.out else Path(EVIDENCE_DIR) / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold cyan]Ingesting pre-fetched pages:[/bold cyan] {result.seed_url}")
    console.print(f"[dim]Evidence packet → {out_dir}[/dim]\n")

    print_summary(result)

    with console.status("[bold green]Building evidence packet…[/bold green]", spinner="dots"):
        packet_dir = build_evidence(
            result,
            out_dir,
            lead_name=args.name or "",
            handle=args.handle or "",
            followers=args.followers,
        )

    console.print(Panel.fit(
        f"[bold green]Evidence packet ready[/bold green]\n"
        f"[bold]{packet_dir / 'packet.md'}[/bold]\n"
        f"{packet_dir / 'evidence.json'}",
        border_style="green",
    ))
    console.print()


def cmd_vision(args: argparse.Namespace) -> None:
    evidence_dir = Path(args.evidence_dir)
    if args.vision_command == "init":
        vision_gate.init_manifest(evidence_dir)
        vision_gate.print_check(evidence_dir)
    elif args.vision_command == "mark":
        marked, unknown = vision_gate.mark_read(evidence_dir, *args.paths)
        for m in marked:
            console.print(f"[green]marked read:[/green] {m}")
        for u in unknown:
            console.print(f"[red]not in manifest, NOT counted:[/red] {u} "
                          f"— run `python main.py vision list {evidence_dir}` to see valid paths")
        if unknown:
            sys.exit(1)
    elif args.vision_command == "check":
        sys.exit(vision_gate.print_check(evidence_dir))
    elif args.vision_command == "list":
        sys.exit(vision_gate.print_list(evidence_dir))


def cmd_crm_gate(args) -> None:
    from audit import crm_gate
    if args.gate == "offer":
        sys.exit(crm_gate.print_offer(args.row_json))
    if args.sends_today is None:
        print("CRM GATE (send): FAIL — --sends-today is required. Run the daily "
              "send-count query against the CRM first; this gate validates what "
              "it's handed, it can't count Notion itself.")
        sys.exit(2)
    sys.exit(crm_gate.print_send(args.row_json, args.sends_today))


def main() -> None:
    parser = argparse.ArgumentParser(prog="funnel-auditor")
    sub = parser.add_subparsers(dest="command")

    p_walk = sub.add_parser("walk", help="crawl + full evidence packet")
    p_walk.add_argument("url")
    p_walk.add_argument("--name", help="lead's name (used for the evidence folder + packet header)")
    p_walk.add_argument("--handle", help="IG handle, e.g. @coachjane")
    p_walk.add_argument("--followers", type=int, help="IG follower count (audience floor input)")
    p_walk.add_argument("--out", help="output dir (default: ./evidence/<slug>/)")
    p_walk.set_defaults(func=cmd_walk)

    p_crawl = sub.add_parser("crawl", help="crawl + terminal summary only")
    p_crawl.add_argument("url")
    p_crawl.set_defaults(func=cmd_crawl)

    p_slug = sub.add_parser("slug", help="print the evidence-folder slug for a name/URL (matches `walk` exactly)")
    p_slug.add_argument("value")
    p_slug.set_defaults(func=cmd_slug)

    p_disc_links = sub.add_parser("discover-links", help="classify a pre-fetched page's links (scope/priority, no fetching)")
    p_disc_links.add_argument("html_file")
    p_disc_links.add_argument("url")
    p_disc_links.add_argument("--platform", help="skip auto-detection (bio-link platform name, or omit)")
    p_disc_links.set_defaults(func=cmd_discover_links)

    p_disc_checkout = sub.add_parser("discover-checkout", help="find checkout/buy links on a pre-fetched sales/course page")
    p_disc_checkout.add_argument("html_file")
    p_disc_checkout.add_argument("url")
    p_disc_checkout.set_defaults(func=cmd_discover_checkout)

    p_ss_name = sub.add_parser("screenshot-name", help="print the exact filename a screenshot should be saved as")
    p_ss_name.add_argument("url")
    p_ss_name.add_argument("suffix", choices=["desktop", "mobile"])
    p_ss_name.set_defaults(func=cmd_screenshot_name)

    p_ingest = sub.add_parser("ingest", help="build the evidence packet from a manifest of pre-fetched pages (Firecrawl path)")
    p_ingest.add_argument("manifest", help="path to the manifest JSON (see main.py module docstring)")
    p_ingest.add_argument("--name", help="lead's name (used for the evidence folder + packet header)")
    p_ingest.add_argument("--handle", help="IG handle, e.g. @coachjane")
    p_ingest.add_argument("--followers", type=int, help="IG follower count (audience floor input)")
    p_ingest.add_argument("--out", help="output dir (default: ./evidence/<slug>/)")
    p_ingest.set_defaults(func=cmd_ingest)

    p_vision = sub.add_parser("vision", help="vision-pass completeness gate (see audit/vision_gate.py)")
    vision_sub = p_vision.add_subparsers(dest="vision_command", required=True)

    v_init = vision_sub.add_parser("init", help="(re)build the manifest from evidence.json + ig/ + hook/")
    v_init.add_argument("evidence_dir")

    v_mark = vision_sub.add_parser("mark", help="mark one or more image paths as read")
    v_mark.add_argument("evidence_dir")
    v_mark.add_argument("paths", nargs="+", help="e.g. ig/1.png screenshots/foo_desktop.png")

    v_check = vision_sub.add_parser("check", help="pass/fail: every required image read? (exit 0/1)")
    v_check.add_argument("evidence_dir")

    v_list = vision_sub.add_parser("list", help="list every tracked image and its read status")
    v_list.add_argument("evidence_dir")

    p_vision.set_defaults(func=cmd_vision)

    p_crm = sub.add_parser(
        "crm-gate",
        help="UAE CRM transition gates: offer (price discovery before any priced offer) "
             "/ send (finding verified + daily cap) — see audit/crm_gate.py",
    )
    p_crm.add_argument("gate", choices=["offer", "send"])
    p_crm.add_argument("row_json", help="path to a JSON dump of the lead row's properties, fetched FRESH from Notion")
    p_crm.add_argument("--sends-today", type=int,
                       help="(send gate) cold sends already logged today, from the daily send-count query")
    p_crm.set_defaults(func=cmd_crm_gate)

    argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        sys.exit(1)
    # Bare URL → walk
    if argv[0] not in (
        "walk", "crawl", "slug", "vision", "crm-gate",
        "discover-links", "discover-checkout", "screenshot-name", "ingest",
        "-h", "--help",
    ):
        argv = ["walk"] + argv

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
