"""Single-query test to verify the limit=0 fix works."""

import asyncio
import os
import json
from src.application.use_cases.scrape_use_case import ScrapeUseCase
from src.infrastructure.scraping.playwright_scraper import PlaywrightGoogleMapsScraper
from src.infrastructure.repositories.json_repository import JsonPlaceRepository
from src.application.dtos.scrape_request import ScrapeRequest


async def test_single_scrape():
    scraper = PlaywrightGoogleMapsScraper(headless=True)
    
    os.makedirs("results/targeted_scrapes", exist_ok=True)
    output_file = "results/targeted_scrapes/TEST_Car_Wrap_Puchong.json"
    
    # Delete if exists
    if os.path.exists(output_file):
        os.remove(output_file)
    
    repository = JsonPlaceRepository(output_path=output_file)
    use_case = ScrapeUseCase(scraper, repository)
    
    # Test with limit=0 (unlimited) — this is the bug we're fixing
    request = ScrapeRequest(
        keyword="Car Wrap",
        location="Puchong",
        limit=0,  # This was causing the 0-results bug
        output_path=output_file
    )
    
    print(f"Testing: '{request.query}' with limit=0 (unlimited)")
    
    try:
        result = await use_case.execute(request)
        print(f"\n=== RESULT ===")
        print(f"Total places collected: {len(result.places)}")
        
        if result.places:
            print(f"✅ FIX VERIFIED — Got {len(result.places)} results!")
            for i, place in enumerate(result.places[:3]):
                print(f"  [{i+1}] {place.name}")
        else:
            print(f"❌ STILL BROKEN — Got 0 results")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_single_scrape())
