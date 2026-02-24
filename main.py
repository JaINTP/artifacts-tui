"""Entry point for the Sentient Artifacts TUI (API-only)."""

from __future__ import annotations

import argparse
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from sentient_artifacts.client.bot_manager_client import BotManagerClient
from sentient_artifacts.client.official_client import OfficialApiClient
from sentient_artifacts.tui.app import TUI


async def _run(url: str | None, token: str | None = None) -> None:
    """Run the TUI against the given API base URL or game token."""
    if token:
        client = OfficialApiClient(token=token)
    elif url:
        client = BotManagerClient(base_url=url)
    else:
        raise ValueError("Either URL or token must be provided.")
        
    tui = TUI(client)
    try:
        await tui.run_async()
    except KeyboardInterrupt:
        pass


def main() -> None:
    """Parse CLI args and launch the TUI."""
    parser = argparse.ArgumentParser(description="Sentient Artifacts TUI")
    parser.add_argument(
        "--url",
        default=None,
        help="Base URL for the bot manager API",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Official Artifacts MMO API token. If passed, the TUI runs in read-only mode using the official API instead of the bot manager.",
    )
    args = parser.parse_args()

    token = args.token or os.environ.get("ARTIFACTS_TOKEN")
    url = args.url

    if not url and not token:
        print("No Bot Manager URL or Game Token provided.")
        print("To use the TUI in view-only mode with the official API, a token is required.")
        try:
            token_input = input("Enter your Artifacts MMO API token (or press Enter to exit): ").strip()
        except KeyboardInterrupt:
            token_input = ""
            print("\nExiting.")
            
        if token_input:
            token = token_input
        else:
            return

    asyncio.run(_run(url, token))


if __name__ == "__main__":
    main()
