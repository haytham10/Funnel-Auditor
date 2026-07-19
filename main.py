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
from audit.urls import slugify
from audit import inboxes, vision_gate

# audit.crawler (Playwright/bs4 stack) is imported lazily inside the commands
# that fetch or parse pages, so the gate commands (crm-gate, send-cap, vision)
# keep working on machines without the crawl dependencies installed.

console = Console()


def print_summary(result: "CrawlResult") -> None:
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
    from audit.crawler import crawl
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
    from audit.crawler import crawl

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
    from audit.crawler import detect_platform, extract_links

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
    from audit.crawler import extract_checkout_links

    html = Path(args.html_file).read_text()
    url = _normalize_url(args.url)
    print(json.dumps(extract_checkout_links(html, url), indent=2))


def cmd_screenshot_name(args: argparse.Namespace) -> None:
    """Prints the exact filename crawl() would have used for this URL +
    suffix (desktop/mobile), so a screenshot fetched by something other
    than Playwright lands under evidence/<slug>/screenshots/ with a name
    the packet renderer and vision-gate path matching already expect."""
    from audit.crawler import _safe_filename

    print(f"{_safe_filename(_normalize_url(args.url))}_{args.suffix}.png")


def _page_from_manifest(entry: dict, manifest_dir: Path) -> "CrawledPage":
    from audit.crawler import CrawledPage

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
    from audit.crawler import CrawlResult
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
        print("CRM GATE (send): FAIL — --sends-today is required: TOTAL sends already "
              "out of the inbox today (all touch types, warm included, both tracks — "
              "count Gmail's sent mail, cross-check the CRM). This gate validates "
              "what it's handed, it can't count Gmail itself.")
        sys.exit(2)
    if args.touch is None:
        print("CRM GATE (send): FAIL — --touch is required (1, 2, or 3). Openers and "
              "follow-ups budget differently: follow-ups due today eat the budget "
              "first, openers get what's left.")
        sys.exit(2)
    if args.touch == 1 and args.followups_due is None:
        print("CRM GATE (send): FAIL — --followups-due is required for a touch 1 "
              "opener: count today's still-unsent follow-ups (warm replies owed, "
              "discovery questions due, cold touch 2/3 due) and hand the number over. "
              "They eat the budget before any new open does.")
        sys.exit(2)
    if args.touch >= 2 and args.carries is None:
        print("CRM GATE (send): FAIL — --carries is required for touch 2/3 "
              "(second-finding | loom-offer | disambiguating-question). A follow-up "
              "that just bumps is a wasted send and a spam signal; declare what new "
              "thing this one carries.")
        sys.exit(2)
    sys.exit(crm_gate.print_send(
        args.row_json, args.sends_today, args.touch, args.followups_due, args.carries,
        inbox=args.inbox, sends_next_day=args.sends_next_day,
    ))


def cmd_send_cap(args) -> None:
    from audit import send_cap
    if args.cap_command == "status":
        sys.exit(send_cap.print_status(inbox=args.inbox, show_all=args.all))
    if args.cap_command == "log":
        sys.exit(send_cap.print_log(args.inbox, args.kind, args.detail))
    sys.exit(send_cap.print_set(args.value, inbox=args.inbox))


def cmd_inbox(args) -> None:
    """Inbox registry management — the seam between logical labels
    (Inbox 1/2/N, used by the CRM, the cap file, and the gate) and the real
    sending addresses + transports. See audit/inboxes.py."""
    from audit import inboxes, send_cap
    if args.inbox_command == "list":
        caps = send_cap.load_all()
        rows = []
        for ib in inboxes.all_inboxes():
            st = caps.get(ib.label)
            if st is None:
                cap_str = "unregistered (fails closed to 20)"
            elif not st.valid:
                # A corrupt entry must not display as a clean ceiling.
                cap_str = f"{st.cap}/day (FAILED CLOSED: {st.problem})"
            else:
                cap_str = f"{st.cap}/day"
            flag = " (primary)" if ib.is_primary else ""
            rows.append({
                "label": ib.label,
                "address": ib.address,
                "send_via": ib.send_via,
                "cap": cap_str,
                "primary": ib.is_primary,
                "note": ib.note + flag,
            })
        print(json.dumps(rows, indent=2))
        sys.exit(0)
    if args.inbox_command == "counts":
        # Today's sent count PER inbox. Direct-API inboxes (gethaytham) are
        # counted here; MCP-only inboxes (Gmail connector) can't be reached
        # from Python, so we emit the exact query for the skill/agent to run.
        # The query uses epoch seconds at Dubai midnight, not a YYYY/MM/DD
        # string: Gmail resolves `after:<date>` in the ACCOUNT's timezone, so
        # a date string can be hours off exactly inside the tick's window.
        from audit import send_cap
        if args.date:
            day_label, boundary = args.date, args.date
        else:
            day_label = send_cap.today().isoformat()
            boundary = str(send_cap.dubai_midnight_epoch())
        query = f"in:sent after:{boundary}"
        scheduled_query = "in:scheduled"
        # The live day (`date` / the `count`) still governs follow-ups and warm
        # replies. A NEW opener queued past noon Dubai can't leave today, so it
        # is attributed to `send_day` and gated against that day's ceiling using
        # the inbox's already-SCHEDULED count (`scheduled`), not `count`. See
        # crm_gate.check_send / `crm-gate send --sends-next-day`.
        send_day = send_cap.send_day().isoformat()
        opener_rolls = send_cap.is_after_send_cutoff() and not args.date
        out = {}
        for ib in inboxes.all_inboxes():
            if ib.send_via == "gmail-gethaytham":
                from audit import gmail_gethaytham as gg
                entry = {"via": ib.send_via, "query": query, "scheduled_query": scheduled_query}
                try:
                    entry["count"] = gg.count_messages(query)
                except Exception as exc:  # noqa: BLE001 - report, never crash the tick
                    entry["count"] = None
                    entry["error"] = str(exc)
                try:
                    entry["scheduled"] = gg.count_messages(scheduled_query)
                except Exception as exc:  # noqa: BLE001 - report, never crash the tick
                    entry["scheduled"] = None
                    entry["scheduled_error"] = str(exc)
                out[ib.label] = entry
            else:
                out[ib.label] = {"count": None, "scheduled": None, "via": ib.send_via,
                                 "query": query, "scheduled_query": scheduled_query,
                                 "note": "count via Gmail MCP: run query for sent messages "
                                         "and scheduled_query for in:scheduled due today"}
        result = {"date": day_label, "send_day": send_day, "inboxes": out}
        if opener_rolls:
            result["opener_note"] = (
                f"past {send_cap.SEND_DAY_CUTOFF_HOUR}:00 Dubai — a NEW opener is attributed to "
                f"send-day {send_day} (tomorrow). Gate it with `crm-gate send --touch 1 "
                "--sends-next-day <that inbox's `scheduled` count>`; follow-ups/warm replies "
                "still count against today's `count`."
            )
        print(json.dumps(result, indent=2))
        sys.exit(0)
    if args.inbox_command == "reconcile":
        if not inboxes.is_registered(args.found_in):
            print(f"INBOX RECONCILE: FAIL — --found-in {args.found_in!r} is not a registered inbox "
                  f"(known: {', '.join(inboxes.labels())})")
            sys.exit(2)
        needs, corrected, reason = inboxes.reconcile_assignment(args.current or None, args.found_in)
        verb = f"SET Inbox = {corrected}" if needs else "no change"
        print(f"INBOX RECONCILE: {verb} — {reason}")
        sys.exit(0)
    if args.inbox_command == "route":
        # Decide which inbox a lead's next send leaves from, given its current
        # assignment (blank for a new lead) and today's per-inbox sent counts.
        caps = {lbl: st.cap for lbl, st in send_cap.load_all().items()}
        counts = {}
        for pair in (args.count or []):
            label, _, n = pair.partition("=")
            # A typo'd label would silently count as 0 sends and hand the
            # router fictional headroom — fail loud instead.
            if not inboxes.is_registered(label):
                print(f"INBOX ROUTE: FAIL — --count label {label!r} is not a registered inbox "
                      f"(known: {', '.join(inboxes.labels())})")
                sys.exit(2)
            try:
                counts[label] = int(n)
            except ValueError:
                print(f"INBOX ROUTE: FAIL — bad --count {pair!r}, expected 'Label=N'")
                sys.exit(2)
        weights = {}
        for pair in (args.weight or []):
            label, _, w = pair.partition("=")
            if not inboxes.is_registered(label):
                print(f"INBOX ROUTE: FAIL — --weight label {label!r} is not a registered inbox "
                      f"(known: {', '.join(inboxes.labels())})")
                sys.exit(2)
            try:
                weights[label] = float(w)
            except ValueError:
                print(f"INBOX ROUTE: FAIL — bad --weight {pair!r}, expected 'Label=0.3'")
                sys.exit(2)
        current = args.current or None
        if current is not None and not inboxes.is_registered(current):
            print(f"INBOX ROUTE: FAIL — current {current!r} is not a registered inbox "
                  f"(known: {', '.join(inboxes.labels())})")
            sys.exit(2)
        policy = args.policy or "headroom"
        chosen = inboxes.choose_inbox(current, caps, counts, policy=policy, weights=weights or None)
        ib = inboxes.resolve(chosen)
        sticky = inboxes.is_registered(current)
        why = "sticky (keeps its assignment)" if sticky else f"{policy} policy"
        rooms = ", ".join(
            f"{lbl} {max(caps.get(lbl, 0) - counts.get(lbl, 0), 0)}" for lbl in inboxes.labels()
        )
        print(f"INBOX ROUTE: {chosen} ({ib.address}, via {ib.send_via}) — {why} (headroom: {rooms})")
        sys.exit(0)


def cmd_dashboard(args) -> None:
    """The command-center dashboard — see audit/dashboard.py.

    `skeleton` prints the Python-reachable base snapshot (per-inbox ceilings +
    Inbox 2's real sent-today count) with every Notion-sourced / Gmail-MCP panel
    seeded as null, PLUS the Gmail-MCP count queries the skill must run. The
    /dashboard skill fills the panels from Notion + Gmail and pipes the completed
    snapshot back into `render`, which validates it and writes the HTML page
    (published as a Claude Artifact). Same trust split as crm-gate: Python owns
    the deterministic pieces, the skill owns the MCP fetches."""
    from audit import dashboard
    if args.dashboard_command == "skeleton":
        print(json.dumps(dashboard.build_skeleton(), indent=2))
        sys.exit(0)
    if args.dashboard_command == "render":
        try:
            snapshot = json.loads(Path(args.snapshot_json).read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"DASHBOARD RENDER: FAIL — cannot read snapshot {args.snapshot_json!r}: {exc}")
            sys.exit(1)
        try:
            html = dashboard.render_html(snapshot, title=args.title)
        except dashboard.DashboardError as exc:
            print(f"DASHBOARD RENDER: FAIL — {exc}")
            sys.exit(1)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        print(f"DASHBOARD RENDER: OK — wrote {out} ({len(html):,} bytes). "
              "Publish it as a Claude Artifact (see the /dashboard skill).")
        sys.exit(0)


def cmd_email_check(args) -> None:
    from audit import email_check
    sys.exit(email_check.print_check(args.address, args.name or ""))


def _apify_quota_note() -> tuple[bool, str | None]:
    """Cheap pre-flight cap read (`apify.account_limits()` — no token cost,
    no actor run). Returns (capped, note). Fails OPEN (capped=False) if the
    check itself errors (missing token, network) — an unreadable quota
    should not block a call that might otherwise succeed; the real call
    surfaces its own error if Apify is actually down."""
    from audit import apify
    try:
        limits = apify.account_limits()
    except apify.ApifyError:
        return False, None
    if limits.get("near_cap"):
        pct = limits.get("pct_of_usd_cap")
        return True, f"Apify at {pct}% of its monthly cap"
    return False, None


def _email_verifier(approved: bool = False):
    """Which verifier `email-verify`/`email-enrich` use. Reads
    `EMAIL_VERIFY_PROVIDER` (default "apify", restored 2026-07-18 now that
    the account is on a paid plan; set to "zerobounce" to force the
    no-Apify path — both providers stay fully wired, this just picks which
    one is preferred). When "apify" is preferred, this checks the Apify
    quota FIRST and auto-falls-back to ZeroBounce if Apify is at/near its
    monthly cap, instead of spending an attempt that would just 402 — no
    manual intervention needed if a plan ever caps out again. An Apify call
    is also cost-gated (see audit/apify.py) — `approved` forwards the
    caller's `--approve-cost` through to `apify.verify_emails`; a call
    whose estimate is unknown or over threshold raises
    ApifyCostApprovalRequired rather than running (ordinary single/batched
    verify calls price out to a fraction of a cent and clear automatically).
    Returns (verify_fn, error_class, note) — `note` is set only when an
    auto-fallback happened, so the caller can fold it into the printed
    gate line rather than silently switching providers."""
    import os
    import functools
    from audit import email_verifier
    provider = os.environ.get("EMAIL_VERIFY_PROVIDER", "apify").strip().lower()
    if provider != "apify":
        return email_verifier.verify_emails, email_verifier.EmailVerifierError, None

    from audit import apify
    capped, note = _apify_quota_note()
    if capped:
        return (email_verifier.verify_emails, email_verifier.EmailVerifierError,
                f"{note} — auto-switched to ZeroBounce for this call")
    return functools.partial(apify.verify_emails, approved=approved), apify.ApifyError, None


def cmd_email_verify(args) -> None:
    """Deliverability verification as a quotable gate line — Apify/
    MillionVerifier by default (restored 2026-07-18, paid plan), or
    ZeroBounce if `EMAIL_VERIFY_PROVIDER=zerobounce` (auto-falling back to
    ZeroBounce if Apify is capped regardless — see `_email_verifier`
    above). This is the confirm step before `Email Verified` is checked
    and the lead becomes sendable — syntax+MX (email-check) is not enough,
    one real bounce burns the domain. One address, one attempt; a
    verifier error is inconclusive (WARN), never a silent pass. An Apify
    call whose estimated cost is unknown or over the $0.10 approval
    threshold prints APPROVAL REQUIRED instead (see audit/apify.py) — get
    Haytham's sign-off, then re-run with `--approve-cost`."""
    from audit import email_check
    from audit.apify import ApifyCostApprovalRequired
    verify_fn, error_cls, note = _email_verifier(approved=args.approve_cost)
    try:
        rows = verify_fn([args.address])
    except ApifyCostApprovalRequired as exc:
        print(f"EMAIL VERIFY: APPROVAL REQUIRED — {exc}")
        sys.exit(3)
    except error_cls as exc:
        print(f"EMAIL VERIFY: WARN — {args.address}: verifier unavailable "
              f"({exc}) — inconclusive, could not confirm deliverability")
        sys.exit(0)
    result = rows[0] if rows else None
    sys.exit(email_check.print_verify(args.address, result, note=note or ""))


def cmd_email_enrich(args) -> None:
    """Nominative email enrichment — the no-email fallback stage. When the walk
    harvested no address, derive name-based candidates against the lead's OWN
    branded domain, verify them in one batched call, and adopt at most one
    deliverable address (never two guessed spellings, never a catch-all guess,
    never a free-provider domain). A PASS line here IS an `EMAIL VERIFY: PASS` on
    the adopted address — authorization to write `Email` and check `Email
    Verified`. Same `EMAIL_VERIFY_PROVIDER` switch (with auto-fallback on a
    capped Apify quota) as `email-verify` — see `_email_verifier`. Fails
    closed: a verifier error is inconclusive (HOLD), never a silent
    adoption. An Apify call whose estimated cost is unknown or over the
    $0.10 approval threshold prints APPROVAL REQUIRED instead of HOLD (see
    audit/apify.py) — get Haytham's sign-off, then re-run with
    `--approve-cost`."""
    from audit import email_enrich
    from audit.urls import registrable_domain
    from audit.apify import ApifyCostApprovalRequired
    verify_fn, error_cls, note = _email_verifier(approved=args.approve_cost)
    try:
        sys.exit(email_enrich.print_enrich(args.name, args.domain, verifier=verify_fn,
                                           note=note or ""))
    except ApifyCostApprovalRequired as exc:
        print(f"EMAIL ENRICH: APPROVAL REQUIRED — "
              f"{registrable_domain(args.domain) or args.domain}: {exc}")
        sys.exit(3)
    except error_cls as exc:
        print(f"EMAIL ENRICH: HOLD — {registrable_domain(args.domain) or args.domain}: "
              f"verifier unavailable ({exc}) — inconclusive, no candidate confirmed")
        sys.exit(0)


def cmd_cta_probe(args) -> None:
    """Single-page Playwright pass: load ONE page and run the JS-button
    click-discovery on it. Exists for the Firecrawl fetch path, where
    cta_clicks is always [] — when the packet shows unverified js_only_buttons
    on an offer page, this resolves just that page instead of re-walking the
    whole funnel with `main.py walk`. Prints the cta_clicks JSON."""
    from audit.crawler import (
        crawl as _unused_guard,  # noqa: F401 — fail fast if the crawl stack is missing
    )
    from audit import crawler

    url = _normalize_url(args.url)
    import os
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        launch_kwargs: dict = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        }
        exe = os.environ.get("FUNNEL_AUDITOR_CHROMIUM")
        if not exe and os.path.exists("/opt/pw-browsers/chromium"):
            exe = "/opt/pw-browsers/chromium"
        if exe:
            launch_kwargs["executable_path"] = exe
        proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        proxied = bool(proxy_url and "127.0.0.1" in proxy_url)
        if proxied:
            launch_kwargs["proxy"] = {"server": proxy_url}
            crawler._ensure_mitm_friendly_tls()
        browser = pw.chromium.launch(**launch_kwargs)
        context = browser.new_context(ignore_https_errors=proxied)
        page = context.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})
        try:
            crawler._goto_with_fallback(page, url)
        except Exception as exc:
            print(json.dumps({"url": url, "error": str(exc)[:200], "cta_clicks": []}, indent=2))
            browser.close()
            sys.exit(1)
        crawler._wait_for_embeds(page)
        clicks = crawler._discover_cta_destinations(page, url, args.type)
        browser.close()
    print(json.dumps({"url": url, "link_type": args.type, "cta_clicks": clicks}, indent=2))


def cmd_gmail_gethaytham(args) -> None:
    """Direct Gmail API path for haytham@gethaytham.com — see
    audit/gmail_gethaytham.py's module docstring for why this exists
    instead of a second Claude connector (Google's Gmail MCP endpoint only
    binds one account and auto-mate.one already claimed it). Prints JSON to
    stdout for the calling skill; errors print {"error": ...} and exit
    non-zero, same contract as `apify`."""
    from audit import gmail_gethaytham as gg

    cmd = args.gg_command
    try:
        if cmd == "search":
            out = gg.search_threads(args.query, max_results=args.max)
        elif cmd == "thread":
            out = gg.get_thread(args.thread_id)
        elif cmd == "message":
            out = gg.get_message(args.message_id)
        elif cmd == "labels":
            out = gg.list_labels()
        elif cmd == "draft":
            body = sys.stdin.read() if args.body == "-" else args.body
            out = gg.create_draft(
                args.to, args.subject, body,
                thread_id=args.thread_id, in_reply_to=args.in_reply_to,
            )
        elif cmd == "drafts":
            out = gg.list_drafts()
        else:
            print(json.dumps({"error": f"gmail-gethaytham: unknown subcommand {cmd!r}"}))
            sys.exit(2)
    except gg.GmailGethaythamError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        sys.exit(1)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


# Manual `apify <cmd>` subcommands that have a no-Apify alternative — when
# the quota is capped, redirect to it instead of letting the actor run 402.
# `ig`/`ig-post`/`li-posts`/`li-profile` are NOT here: Firecrawl can't reach
# either platform, so there is nothing to redirect to and they must run
# regardless of cap status (blocking them would just strand hook-finding
# with no fallback at all).
_APIFY_ALTERNATIVES = {
    "verify-email": "`python main.py email-verify <address>` (ZeroBounce, no Apify cost)",
    "search": "`firecrawl_search` + `python main.py classify-footprint` (no Apify cost)",
    "footprint": "`firecrawl_search` + `python main.py classify-footprint` (no Apify cost)",
}


def cmd_apify(args) -> None:
    """No-login third-party fetch layer — LinkedIn/Instagram hooks, email
    verification, Google SERP (see audit/apify.py). Prints JSON to stdout
    for the calling skill; errors print {"error": ...} and exit non-zero.
    `verify-email`/`search`/`footprint` check the quota first and redirect
    to their no-Apify alternative if capped, rather than running into a 402
    — see `_APIFY_ALTERNATIVES`. There's no such redirect for `ig`/
    `li-posts`/`li-profile`/`youtube`: those have no substitute, so they always run.

    Every run is also cost-gated (audit/apify.py's approval threshold,
    $0.10): a call whose estimated cost is unknown or over threshold
    prints `{"error": ..., "needs_approval": true, "estimated_usd": ...}`
    and exits 3 instead of running — get Haytham's approval, then re-run
    the same command with `--approve-cost`."""
    from audit import apify

    cmd = args.apify_command
    approved = getattr(args, "approve_cost", False)
    try:
        if cmd == "limits":
            out = apify.account_limits()
        elif cmd == "actors":
            out = apify.discover_actors(args.query, args.limit)
        elif cmd in _APIFY_ALTERNATIVES and _apify_quota_note()[0]:
            print(json.dumps({
                "error": f"Apify is at/near its monthly cap — use "
                         f"{_APIFY_ALTERNATIVES[cmd]} instead",
            }, indent=2))
            sys.exit(1)
        elif cmd == "ig":
            out = apify.instagram(args.url, mode=args.mode, newer_than=args.newer_than,
                                  limit=args.limit, skip_pinned=args.skip_pinned,
                                  include_about=args.include_about, raw=args.raw,
                                  approved=approved)
        elif cmd == "ig-post":
            out = apify.instagram_post(args.url, raw=args.raw, approved=approved)
        elif cmd == "li-posts":
            out = apify.linkedin_posts(args.url, max_posts=args.max, since=args.since,
                                       raw=args.raw, approved=approved)
        elif cmd == "li-profile":
            out = apify.linkedin_profile(args.url, with_email=args.email, raw=args.raw,
                                         approved=approved)
        elif cmd == "youtube":
            out = apify.youtube_channel(args.channel, raw=args.raw, approved=approved)
        elif cmd == "verify-email":
            out = apify.verify_emails(args.addresses, raw=args.raw, approved=approved)
        elif cmd == "search":
            out = apify.google_search(args.query, pages=args.pages, site=args.site,
                                      country=args.country, raw=args.raw, approved=approved,
                                      meta=getattr(args, "meta", False))
        elif cmd == "footprint":
            out = apify.footprint_search(args.platform, geo=args.geo, role=args.role,
                                         country=args.country, raw=args.raw, approved=approved)
        else:
            parser_error = f"apify: unknown subcommand {cmd!r}"
            print(json.dumps({"error": parser_error}))
            sys.exit(2)
    except apify.ApifyCostApprovalRequired as exc:
        print(json.dumps({
            "error": str(exc),
            "needs_approval": True,
            "actor": exc.actor_id,
            "estimated_usd": exc.estimated_usd,
        }, indent=2))
        sys.exit(3)
    except apify.ApifyError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        sys.exit(1)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


def cmd_classify_footprint(args) -> None:
    """Fetch-agnostic footprint merge (audit/footprint.py) — the Firecrawl-fed
    replacement for `apify footprint`. Takes hit lists already fetched by the
    skill via `firecrawl_search` for both query shapes (subdomain + 'powered
    by' marker) and does the same dedupe/noise-filter/tagging Apify's
    google-search-scraper used to feed, at no Apify cost. Prints JSON;
    unknown platform or unreadable input prints {"error": ...} and exits
    non-zero, same contract as `apify`."""
    from audit import footprint

    def _load_hits(path: str | None) -> list[dict]:
        if not path:
            return []
        text = sys.stdin.read() if path == "-" else Path(path).read_text()
        return json.loads(text) if text.strip() else []

    try:
        subdomain_hits = _load_hits(args.subdomain_hits)
        marker_hits = _load_hits(args.marker_hits)
        out = footprint.classify_footprint_hits(
            args.platform, subdomain_hits, marker_hits,
            geo=args.geo, role=args.role,
        )
    except (footprint.FootprintError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        sys.exit(1)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


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
             "/ send (finding verified + follow-ups-first daily ceiling + touch 2/3 "
             "carrier check) — see audit/crm_gate.py",
    )
    p_crm.add_argument("gate", choices=["offer", "send"])
    p_crm.add_argument("row_json", help="path to a JSON dump of the lead row's properties, fetched FRESH from Notion")
    p_crm.add_argument("--sends-today", type=int,
                       help="(send gate) TOTAL sends already out of the inbox today — all touch "
                            "types, warm included, both tracks (Gmail sent count)")
    p_crm.add_argument("--touch", type=int,
                       help="(send gate) which cold touch this send is: 1, 2, or 3 (the sequence "
                            "is three touches, day 0/3/9, then Dormant)")
    p_crm.add_argument("--followups-due", type=int,
                       help="(send gate, touch 1) follow-ups still owed on the opener's send-day — "
                            "they eat the budget before any opener")
    p_crm.add_argument("--sends-next-day", type=int, default=None,
                       help="(send gate, touch 1) tomorrow's already-scheduled sends out of this "
                            "inbox. Required past noon Dubai: a fresh opener queued after noon is "
                            "scheduled for tomorrow morning, so it is gated against TOMORROW's "
                            "ceiling using this count, not today's already-spent one")
    p_crm.add_argument("--carries", choices=["second-finding", "loom-offer", "disambiguating-question"],
                       help="(send gate, touch 2/3) the new thing this follow-up carries; "
                            "second-finding is checked against the row's Findings Bank")
    p_crm.add_argument("--inbox", default=None,
                       help="(send gate) which sending inbox this send leaves from — its ceiling is "
                            "independent (default: primary, haytham@auto-mate.one)")
    p_crm.set_defaults(func=cmd_crm_gate)

    p_cap = sub.add_parser(
        "send-cap",
        help="daily send ceiling, one independent ramp PER inbox (TOTAL sends leaving that "
             "inbox): status shows a cap + ramp reminder (--inbox to target one, --all for "
             "every inbox); set moves one step (20 → 25 → 30) or registers a new inbox at 20, "
             "Haytham's call only — see audit/send_cap.py",
    )
    cap_sub = p_cap.add_subparsers(dest="cap_command", required=True)
    c_status = cap_sub.add_parser("status", help="print the current ceiling, days at this step, and the ramp reminder")
    c_status.add_argument("--inbox", default=None,
                          help="which sending inbox by logical label (default: primary, 'Inbox 1')")
    c_status.add_argument("--all", action="store_true",
                          help="show every registered inbox and the total additive system ceiling")
    c_set = cap_sub.add_parser("set", help="move an inbox's ceiling to a ramp step (20/25/30), or register a new inbox at 20 — Haytham's call, never a skill's")
    c_set.add_argument("value", type=int)
    c_set.add_argument("--inbox", default=None,
                       help="which sending inbox by logical label (default: primary); must already be in the registry")
    c_log = cap_sub.add_parser(
        "log",
        help="append one canonical per-inbox line to docs/deliverability-log.md (the ramp evidence file)",
    )
    c_log.add_argument("--inbox", required=True, help="the inbox this event concerns (logical label)")
    c_log.add_argument("--kind", required=True,
                       choices=["bounce", "spam-flag", "test-score", "over-ceiling", "note"],
                       help="event type")
    c_log.add_argument("--detail", required=True, help="one-line detail (address, score, count, etc.)")
    p_cap.set_defaults(func=cmd_send_cap)

    p_inbox = sub.add_parser(
        "inbox",
        help="inbox registry — the seam between logical labels (Inbox 1/2/N, used by the CRM, "
             "the cap file, and the gate) and real sending addresses + transports. `list` shows "
             "every inbox with its address, transport, and cap; `route` picks the inbox for a "
             "lead's next send — see audit/inboxes.py",
    )
    inbox_sub = p_inbox.add_subparsers(dest="inbox_command", required=True)
    inbox_sub.add_parser("list", help="every registered inbox: label, address, transport, cap (JSON)")
    i_route = inbox_sub.add_parser(
        "route",
        help="which inbox a lead's next send leaves from, given its current assignment and today's counts",
    )
    i_route.add_argument("--current", default=None,
                         help="the lead's current Inbox label (blank/omitted for a new, unassigned lead)")
    i_route.add_argument("--count", action="append", metavar="LABEL=N",
                         help="today's sends already out of an inbox, e.g. --count 'Inbox 1=18' "
                              "(repeatable; missing inboxes count 0)")
    i_route.add_argument("--policy", default="headroom", choices=list(inboxes.ROUTING_POLICIES),
                         help="routing policy for a NEW lead: headroom (emptiest inbox, default) "
                              "or fill-primary (fill primary, then overflow)")
    i_route.add_argument("--weight", action="append", metavar="LABEL=W",
                         help="warm-up bias for the headroom policy, e.g. --weight 'Inbox 2=0.3' "
                              "(scales that inbox's effective headroom down while it warms; "
                              "repeatable; missing = 1.0)")
    i_counts = inbox_sub.add_parser(
        "counts",
        help="today's sent count per inbox — counts direct-API inboxes (gethaytham) here, "
             "emits the query for Gmail MCP inboxes; queries by epoch seconds at Dubai "
             "midnight (timezone-exact, unlike after:YYYY/MM/DD)",
    )
    i_counts.add_argument("--date", default=None, metavar="YYYY/MM/DD",
                          help="override the query boundary with a Gmail-style date string "
                               "(default: epoch seconds at Dubai midnight today, timezone-exact)")
    i_rec = inbox_sub.add_parser(
        "reconcile",
        help="reconcile a lead's CRM Inbox against where its thread physically lives (reality wins)",
    )
    i_rec.add_argument("--current", default=None, help="the lead's current CRM Inbox label (may be blank)")
    i_rec.add_argument("--found-in", required=True, help="the inbox whose Gmail actually holds the thread")
    p_inbox.set_defaults(func=cmd_inbox)

    p_dash = sub.add_parser(
        "dashboard",
        help="command-center dashboard: `skeleton` prints the Python-reachable base "
             "snapshot (per-inbox ceilings + Inbox 2's sent-today count) + the Gmail-MCP "
             "count queries, with Notion panels seeded null for the skill to fill; "
             "`render` validates a completed snapshot and writes the self-contained HTML "
             "page (published as a Claude Artifact) — see audit/dashboard.py",
    )
    dash_sub = p_dash.add_subparsers(dest="dashboard_command", required=True)
    dash_sub.add_parser(
        "skeleton",
        help="print the Python-reachable base snapshot JSON (fill the null panels from "
             "Notion + Gmail MCP, then pipe into `render`)",
    )
    d_render = dash_sub.add_parser(
        "render", help="validate a completed snapshot JSON and write the dashboard HTML")
    d_render.add_argument("snapshot_json", help="path to the completed snapshot JSON")
    d_render.add_argument("--out", required=True, help="output path for the HTML page")
    d_render.add_argument("--title", default="Funnel Auditor — Command Center",
                          help="page title (browser tab + Artifact name)")
    p_dash.set_defaults(func=cmd_dashboard)

    p_email = sub.add_parser(
        "email-check",
        help="pre-send address check: syntax + MX + typo/disposable/role flags "
             "(FAIL = don't send; WARN inconclusive = verify via "
             "`email-verify`) — see audit/email_check.py",
    )
    p_email.add_argument("address")
    p_email.add_argument("--name", help="lead's name — flags whether the local part matches")
    p_email.set_defaults(func=cmd_email_check)

    p_email_verify = sub.add_parser(
        "email-verify",
        help="deliverability verification (ZeroBounce, audit/email_verifier.py) as a "
             "quotable gate line: PASS = mailbox confirmed, check `Email Verified` and "
             "the lead is sendable; FAIL = bounce risk, never send; WARN = inconclusive "
             "(catch_all/unknown), Haytham's call. The confirm step email-check can't "
             "do — see audit/email_check.py",
    )
    p_email_verify.add_argument("address")
    p_email_verify.add_argument("--approve-cost", action="store_true",
                                help="Haytham has approved this call's estimated Apify cost "
                                     "(only relevant when EMAIL_VERIFY_PROVIDER=apify and the "
                                     "estimate is over $0.10 — see audit/apify.py)")
    p_email_verify.set_defaults(func=cmd_email_verify)

    p_email_enrich = sub.add_parser(
        "email-enrich",
        help="nominative fallback when no address was harvested: derive name-based "
             "candidates against the lead's own domain, verify them in one batched "
             "call, adopt at most ONE deliverable address. PASS = an EMAIL VERIFY: "
             "PASS on that address (check `Email Verified`); HOLD = catch-all/"
             "inconclusive, no auto-send; NONE = nothing verified or free-provider "
             "domain — see audit/email_enrich.py",
    )
    p_email_enrich.add_argument("name", help="the lead's full name (Contact Name)")
    p_email_enrich.add_argument("domain", help="the lead's Site URL or bare branded domain")
    p_email_enrich.add_argument("--approve-cost", action="store_true",
                                help="Haytham has approved this call's estimated Apify cost "
                                     "(only relevant when EMAIL_VERIFY_PROVIDER=apify and the "
                                     "estimate is over $0.10 — see audit/apify.py)")
    p_email_enrich.set_defaults(func=cmd_email_enrich)

    p_probe = sub.add_parser(
        "cta-probe",
        help="single-page Playwright JS-button click-discovery, for resolving one "
             "Firecrawl-fetched page's unverified buttons without re-walking the funnel",
    )
    p_probe.add_argument("url")
    p_probe.add_argument("--type", default="sales", choices=["sales", "course", "booking"],
                         help="the page's link_type (click scope excludes checkout pages by design)")
    p_probe.set_defaults(func=cmd_cta_probe)

    p_apify = sub.add_parser(
        "apify",
        help="no-login third-party fetch layer: LinkedIn/Instagram hook evidence "
             "(the default use — email verification and Google SERP now default "
             "elsewhere, `email-verify`/`classify-footprint`; `verify-email`/`search`/"
             "`footprint` here remain a manual fallback). See audit/apify.py. Reads "
             "APIFY_TOKEN from the environment.",
    )
    apify_sub = p_apify.add_subparsers(dest="apify_command", required=True)

    apify_sub.add_parser(
        "limits",
        help="current monthly usage vs. plan limits — check ONCE before a batch "
             "so a dead quota isn't rediscovered by every lead independently",
    )

    a_actors = apify_sub.add_parser("actors", help="search the public Apify Store (no token needed)")
    a_actors.add_argument("query")
    a_actors.add_argument("--limit", type=int, default=6)

    a_ig = apify_sub.add_parser("ig", help="Instagram: recent posts w/ captions (post scraper), or profile details (profile scraper)")
    a_ig.add_argument("url", help="profile URL or @handle (post URL also works for --mode posts)")
    a_ig.add_argument("--mode", default="posts",
                      choices=["posts", "details"],
                      help="posts = feed w/ captions (instagram-post-scraper); "
                           "details = follower/bio metadata (instagram-profile-scraper)")
    a_ig.add_argument("--newer-than", dest="newer_than",
                      help="recency filter for posts mode, e.g. '7 days', '2 months', or 2026-07-01")
    a_ig.add_argument("--limit", type=int, default=12, help="max posts (posts mode)")
    a_ig.add_argument("--skip-pinned", dest="skip_pinned", action="store_true",
                      help="posts mode: drop pinned posts (default keeps them — a pinned "
                           "post is often the coach's signature/framework content)")
    a_ig.add_argument("--include-about", dest="include_about", action="store_true",
                      help="details mode: add the paid about-account block "
                           "(country, join date, verification)")
    a_ig.add_argument("--raw", action="store_true", help="skip field trimming")
    a_ig.add_argument("--approve-cost", action="store_true",
                      help="Haytham has approved this run's estimated cost (only needed if "
                           "it's over $0.10 — see audit/apify.py's cost approval gate)")

    a_igp = apify_sub.add_parser("ig-post", help="full detail on one Instagram post (caption + top comments)")
    a_igp.add_argument("url")
    a_igp.add_argument("--raw", action="store_true")
    a_igp.add_argument("--approve-cost", action="store_true",
                       help="Haytham has approved this run's estimated cost (only needed if "
                            "it's over $0.10 — see audit/apify.py's cost approval gate)")

    a_lip = apify_sub.add_parser("li-posts", help="recent LinkedIn posts (no cookies) — primary hook source")
    a_lip.add_argument("url")
    a_lip.add_argument("--max", type=int, default=5, help="max posts (default 5)")
    a_lip.add_argument("--since",
                       choices=["any", "1h", "24h", "week", "month", "3months", "6months", "year"],
                       help="recency window, e.g. week, month")
    a_lip.add_argument("--raw", action="store_true")
    a_lip.add_argument("--approve-cost", action="store_true",
                       help="Haytham has approved this run's estimated cost (only needed if "
                            "it's over $0.10 — see audit/apify.py's cost approval gate)")

    a_lipr = apify_sub.add_parser("li-profile", help="LinkedIn profile enrichment (headline/about/experience)")
    a_lipr.add_argument("url")
    a_lipr.add_argument("--email", action="store_true",
                        help="use the email-search mode ($10/1k) to find an address — no-email leads only")
    a_lipr.add_argument("--raw", action="store_true")
    a_lipr.add_argument("--approve-cost", action="store_true",
                        help="Haytham has approved this run's estimated cost (only needed if "
                             "it's over $0.10 — see audit/apify.py's cost approval gate)")

    a_yt = apify_sub.add_parser("youtube", help="YouTube channel info — subscriber count + stats (the audience-floor number Firecrawl can't read for YT-native coaches)")
    a_yt.add_argument("channel", help="channel URL or @handle")
    a_yt.add_argument("--raw", action="store_true")
    a_yt.add_argument("--approve-cost", action="store_true",
                      help="Haytham has approved this run's estimated cost (only needed if "
                           "it's over $0.10 — see audit/apify.py's cost approval gate)")

    a_ver = apify_sub.add_parser("verify-email", help="verify one or more addresses before they enter the CRM")
    a_ver.add_argument("addresses", nargs="+")
    a_ver.add_argument("--raw", action="store_true")
    a_ver.add_argument("--approve-cost", action="store_true",
                       help="Haytham has approved this run's estimated cost (only needed if "
                            "it's over $0.10 — see audit/apify.py's cost approval gate)")

    a_search = apify_sub.add_parser("search", help="Google SERP for one query")
    a_search.add_argument("query")
    a_search.add_argument("--pages", type=int, default=1)
    a_search.add_argument("--site", help="scope to a domain, e.g. linkedin.com")
    a_search.add_argument("--country", default="ae", help="country bias (default ae); pass '' to disable")
    a_search.add_argument("--meta", action="store_true",
                          help="also return relatedQueries + peopleAlsoAsk (query expansion)")
    a_search.add_argument("--raw", action="store_true")
    a_search.add_argument("--approve-cost", action="store_true",
                          help="Haytham has approved this run's estimated cost (only needed if "
                               "it's over $0.10 — see audit/apify.py's cost approval gate)")

    a_footprint = apify_sub.add_parser(
        "footprint",
        help="platform footprint sourcing: subdomain + 'powered by' footer signature, merged")
    a_footprint.add_argument("platform",
                             help="kajabi | teachable | thinkific | podia | systeme | kartra | skool")
    a_footprint.add_argument("--geo", default="Dubai",
                             help="geographic marker (default Dubai; also Abu Dhabi, Sharjah, UAE)")
    a_footprint.add_argument("--role", default="coach",
                             help="role/noun to search for (default coach)")
    a_footprint.add_argument("--country", default="ae", help="country bias (default ae); pass '' to disable")
    a_footprint.add_argument("--raw", action="store_true")
    a_footprint.add_argument("--approve-cost", action="store_true",
                             help="Haytham has approved this run's estimated cost (only needed if "
                                  "it's over $0.10 — see audit/apify.py's cost approval gate)")

    p_apify.set_defaults(func=cmd_apify)

    p_classify_fp = sub.add_parser(
        "classify-footprint",
        help="merge pre-fetched Firecrawl search hits into a deduped, tagged "
             "platform-footprint result (audit/footprint.py) — the default, "
             "no-Apify-cost replacement for `apify footprint`",
    )
    p_classify_fp.add_argument("platform",
                               help="kajabi | teachable | thinkific | podia | systeme | kartra | skool")
    p_classify_fp.add_argument("--subdomain-hits",
                               help="JSON file (or '-' for stdin) of hits from the site:<domain> query")
    p_classify_fp.add_argument("--marker-hits",
                               help="JSON file (or '-' for stdin) of hits from the "
                                    "'powered by <platform>' query")
    p_classify_fp.add_argument("--geo", default="Dubai",
                               help="geographic marker (default Dubai; also Abu Dhabi, Sharjah, UAE)")
    p_classify_fp.add_argument("--role", default="coach",
                               help="role/noun searched for (default coach)")
    p_classify_fp.set_defaults(func=cmd_classify_footprint)

    p_gg = sub.add_parser(
        "gmail-gethaytham",
        help="direct Gmail API for haytham@gethaytham.com (the second UAE send "
             "inbox) — no Claude connector involved, since Google's Gmail MCP "
             "endpoint only binds one account and auto-mate.one already claimed "
             "it. Reads GETHAYTHAM_GMAIL_CLIENT_ID / _CLIENT_SECRET / "
             "_REFRESH_TOKEN from the environment — see audit/gmail_gethaytham.py.",
    )
    gg_sub = p_gg.add_subparsers(dest="gg_command", required=True)

    gg_search = gg_sub.add_parser("search", help="search threads (Gmail query syntax)")
    gg_search.add_argument("query")
    gg_search.add_argument("--max", type=int, default=10)

    gg_thread = gg_sub.add_parser("thread", help="fetch one thread, full format")
    gg_thread.add_argument("thread_id")

    gg_message = gg_sub.add_parser("message", help="fetch one message, full format")
    gg_message.add_argument("message_id")

    gg_sub.add_parser("labels", help="list labels")

    gg_draft = gg_sub.add_parser("draft", help="create a Gmail DRAFT (never sends)")
    gg_draft.add_argument("to")
    gg_draft.add_argument("subject")
    gg_draft.add_argument("body", help="plain-text body, or '-' to read from stdin")
    gg_draft.add_argument("--thread-id", help="keep this draft in an existing thread")
    gg_draft.add_argument("--in-reply-to", help="Message-Id header of the message being replied to")

    gg_sub.add_parser("drafts", help="list existing drafts")

    p_gg.set_defaults(func=cmd_gmail_gethaytham)

    argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        sys.exit(1)
    # Bare URL → walk
    if argv[0] not in (
        "walk", "crawl", "slug", "vision", "crm-gate", "send-cap", "inbox",
        "dashboard", "email-check", "email-verify", "email-enrich", "cta-probe", "apify",
        "classify-footprint", "gmail-gethaytham", "discover-links", "discover-checkout",
        "screenshot-name", "ingest", "-h", "--help",
    ):
        argv = ["walk"] + argv

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
