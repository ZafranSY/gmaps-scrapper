"""CLI Argument Parser — infrastructure adapter for command-line input.

This module provides the logic for parsing command-line arguments and
transforming them into the application-layer ScrapeRequest DTO.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.application.dtos.scrape_request import ScrapeRequest


def build_parser() -> argparse.ArgumentParser:
    """Construct the ArgumentParser for the gmaps-scraper CLI.

    Configures the tool name, description, and positional/optional arguments.
    It uses RawDescriptionHelpFormatter to preserve the formatting of the epilog.

    Returns:
        argparse.ArgumentParser: A configured argument parser instance.
    """
    description = "🔥 gmaps-scraper: A robust Clean Architecture Google Maps scraper."
    
    epilog = """
Usage Examples:
  python src/main.py "coffee shops" "Kuala Lumpur"
  python src/main.py "restaurants" "George Town" --limit 50 --output food.json
  python src/main.py "dentists" "Subang Jaya" --verbose --headless
    """

    parser = argparse.ArgumentParser(
        prog="gmaps-scraper",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Positional Arguments
    parser.add_argument(
        "keyword", 
        type=str, 
        help="The search term (e.g., 'bakery', 'dentist')."
    )
    parser.add_argument(
        "location", 
        type=str, 
        help="The location to search in (e.g., 'Kuala Lumpur', 'Penang')."
    )

    # Optional Arguments
    parser.add_argument(
        "--limit", 
        type=int, 
        default=200, 
        help="Maximum number of results to collect (default: 200)."
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("results.json"),
        dest="output_path",
        help="Path to the output JSON file (default: results.json)."
    )
    parser.add_argument(
        "--headless", 
        action="store_true", 
        help="Run the browser in headless mode (no window visible)."
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable detailed debug logging."
    )

    return parser


def parse_args(argv: list[str] | None = None) -> ScrapeRequest:
    """Parse raw arguments into a validated ScrapeRequest DTO.

    This function calls the parser, performs early domain validation on the
    limit, and handles input edge cases.

    Args:
        argv (list[str], optional): Custom list of arguments for testing. 
            Defaults to sys.argv[1:].

    Returns:
        ScrapeRequest: The domain-agnostic request parameters.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Simple domain validation
    if args.limit < 1:
        parser.error("Limit must be at least 1.")

    # Practical cap to prevent excessive resource usage
    if args.limit > 1000:
        print(
            "⚠️  Warning: Limit exceeds 1000. Capping at 1000 to maintain stability.", 
            file=sys.stderr
        )
        args.limit = 1000

    return ScrapeRequest(
        keyword=args.keyword,
        location=args.location,
        limit=args.limit,
        output_path=args.output_path,
        headless=args.headless,
        verbose=args.verbose
    )
