"""Interactive CLI for the Instagram Brand Research Assistant."""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.prompt import Prompt

from instagram_agent.agents.discovery import DiscoveryAgent
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.logging_utils import setup_logging
from instagram_agent.pipelines.analyse_profile import analyse_profile
from instagram_agent.pipelines.discover_and_research import discover_and_research

console = Console()


def _print_menu() -> None:
    console.print("\n[bold]Instagram Brand Research Assistant[/bold]")
    console.print("1 Discover creators")
    console.print("2 Analyse profile")
    console.print("3 Brand research")
    console.print("4 Export report")
    console.print("5 Quit\n")


async def _discover() -> None:
    query = Prompt.ask("Search query", default="upcycled bags")
    result = await DiscoveryAgent().discover(query)
    console.print(f"\nDiscovered {len(result.profile_urls)} profiles:")
    for url in result.profile_urls:
        console.print(f"- {url}")


async def _analyse() -> None:
    url = Prompt.ask(
        "Instagram profile URL",
        default="https://www.instagram.com/patagonia/",
    )
    result = await analyse_profile(url)
    console.print(f"\nName: {result.profile.name}")
    console.print(f"Followers: {result.profile.followers}")
    console.print(f"Score: {result.analysis.score}")
    console.print(f"Follow: {result.analysis.follow}")
    console.print(f"Reason: {result.analysis.reason}")


async def _brand_research() -> None:
    query = Prompt.ask("Search query", default="upcycled bags")
    brand = build_jollyzu_brand()
    console.print(f"Using brand profile: [bold]{brand.name}[/bold]")
    results = await discover_and_research(query, brand)
    console.print(f"\nResearched {len(results)} creators (sorted by brand_fit):")
    for item in results[:10]:
        console.print(
            f"- {item.profile.name}: brand_fit={item.research.brand_fit} "
            f"confidence={item.research.confidence}"
        )


async def _export_report() -> None:
    console.print(
        "Export runs brand research for a query, then writes CSV + Markdown + JSON."
    )
    query = Prompt.ask("Search query", default="upcycled bags")
    brand = build_jollyzu_brand()
    results = await discover_and_research(query, brand)
    console.print(f"Exported {len(results)} rows to outputs/csv and outputs/reports.")


async def run_cli() -> None:
    """Run the interactive menu loop."""
    setup_logging()
    while True:
        _print_menu()
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        try:
            if choice == "1":
                await _discover()
            elif choice == "2":
                await _analyse()
            elif choice == "3":
                await _brand_research()
            elif choice == "4":
                await _export_report()
            else:
                console.print("Goodbye.")
                return
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Error:[/red] {type(exc).__name__}: {exc}")


def main() -> None:
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
