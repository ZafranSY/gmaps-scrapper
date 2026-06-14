"""CLI Entrypoint — coordinates application wiring and execution.

This module is the outermost layer of the application (Interfaces). It is 
responsible for configuring logging, parsing arguments, and performing 
manual dependency injection to wire the concrete infrastructure adapters 
to the application use cases.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path

from src.application.use_cases.scrape_use_case import ScrapeUseCase
from src.infrastructure.cli.argument_parser import parse_args
from src.infrastructure.repositories.json_repository import JsonPlaceRepository
from src.infrastructure.scraping.playwright_scraper import PlaywrightGoogleMapsScraper


def _configure_logging(verbose: bool) -> None:
    """Configure system-wide logging levels and formatting.

    Args:
        verbose (bool): If True, set level to DEBUG, else INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr
    )
    
    # Silence noisy third-party libraries unless in verbose mode
    if not verbose:
        logging.getLogger("playwright").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)


def _print_banner(query: str, limit: int, output: Path, headless: bool) -> None:
    """Print an aesthetic startup banner to the terminal.

    Args:
        query (str): The search query.
        limit (int): The result collection limit.
        output (Path): The destination file path.
        headless (bool): Whether the browser is hidden.
    """
    separator = "=" * 60
    print(separator)
    print("🌍 gmaps-scraper | Clean Architecture Scraper")
    print(separator)
    print(f"🔍 Search Query : {query}")
    print(f"📊 Target Limit  : {limit}")
    print(f"💾 Output File  : {output}")
    print(f"🌐 Browser Mode : {'Headless' if headless else 'Headed'}")
    print(separator)


def _validate_output_path(output_path: Path) -> None:
    """Fail fast if the output path is not writable.

    Creates parent directories if needed, then attempts a trial write.
    Exits with code 1 if the check fails.

    Args:
        output_path (Path): The destination file path for JSON output.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Trial write to verify permissions
        with open(output_path, "a") as fh:
            pass
    except (PermissionError, OSError) as exc:
        print(f"❌ Cannot write to {output_path}: {exc}", file=sys.stderr)
        sys.exit(1)


def run() -> int:
    """Main CLI execution loop.

    Wires dependencies, defines the execution context, and handles global 
    exceptions.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    # 1. Parse arguments into our Request DTO
    try:
        request = parse_args()
    except Exception as exc:
        print(f"❌ Argument error: {exc}", file=sys.stderr)
        return 1
        
    # 2. Setup environment
    _configure_logging(request.verbose)
    _print_banner(request.query, request.limit, request.output_path, request.headless)
    
    # 2.5 Validate output path early — fail fast before scraping
    _validate_output_path(request.output_path)
    
    # 3. Manual Dependency Injection (Wiring)
    scraper = PlaywrightGoogleMapsScraper(
        headless=request.headless, 
        verbose=request.verbose
    )
    repository = JsonPlaceRepository(output_path=request.output_path)
    use_case = ScrapeUseCase(scraper=scraper, repository=repository)
    
    # 4. Execute the workflow
    start_time = time.monotonic()
    try:
        result = asyncio.run(use_case.execute(request))
        
        elapsed = time.monotonic() - start_time
        print("=" * 60)
        print(f"🏁 Scrape Complete!")
        print(f"✅ Total Collected: {result.total_collected}")
        print(f"⏱️  Elapsed Time   : {elapsed:.1f}s")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Scrape aborted by user.", file=sys.stderr)
        return 1
    except Exception as exc:
        logging.exception("An unexpected error occurred during execution.")
        print(f"❌ Fatal Error: {exc}", file=sys.stderr)
        return 1
