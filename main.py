"""
Funnel Auditor — CLI entry point.

Usage:
    python main.py <url>
"""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from audit.crawler import crawl, CrawlResult

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
    console.print(
        f"[bold]Pages crawled:[/bold] {len(result.pages)}   "
        f"[bold]Screenshots saved to:[/bold] [dim]./screenshots/[/dim]"
    )
    console.print()


def main() -> None:
    if len(sys.argv) < 2:
        console.print("[red]Usage: python main.py <url>[/red]")
        sys.exit(1)

    url = sys.argv[1].strip()
    if not url.startswith("http"):
        url = "https://" + url

    console.print(f"\n[bold cyan]Starting crawl:[/bold cyan] {url}\n")

    with console.status("[bold green]Crawling funnel…[/bold green]", spinner="dots"):
        result = crawl(url)

    print_summary(result)


if __name__ == "__main__":
    main()
