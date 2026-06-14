"""
Main entry point for gmaps-scraper.

Run via: python src/main.py "keyword" "location" --limit 10

All business logic resides in src/application/, and all scraping 
infrastructure is located in src/infrastructure/scraping/.
"""
import os
import sys

# Ensure the project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.interfaces.cli_entrypoint import run

if __name__ == "__main__":
    sys.exit(run())
