
import asyncio
import os
import json
from datetime import datetime
from src.application.use_cases.scrape_use_case import ScrapeUseCase
from src.infrastructure.scraping.playwright_scraper import PlaywrightGoogleMapsScraper
from src.infrastructure.repositories.json_repository import JsonPlaceRepository
from src.application.dtos.scrape_request import ScrapeRequest

HUBS = [
    # Top Priority
    "Bukit Mertajam", "Sungai Pinang, Georgetown", "Tanjung Tokong",
    # Main Hubs
    "Bandar Sunway", "Glenmarie", "Pavilion Kuala Lumpur", "Golden Triangle KL",
    "Mount Austin JB", "Juru Auto City", "Mont Kiara", "Bangsar", "Damansara",
    "Malim Jaya Melaka", "Seremban 2", "Jelapang Perak", "Sungai Petani",
    "Kangar Perlis", "Padang Besar",
    # Additional Rich Areas
    "Puchong", "Sri Hartamas", "TTDI"
]

TERMS = [
    "Car Tinted", "Car Wrap", "Auto Detailing", "Paint Protection Film",
    "Kedai Tinted", "Car Coating", "Car Accessories", "Pasang Tinted",
    "Car Workshop", "Premium Car Wash"
]

async def run_targeted_scrape():
    # Setup scraper once
    scraper = PlaywrightGoogleMapsScraper(headless=True)
    
    # Create results directory
    results_dir = "results/targeted_scrapes"
    os.makedirs(results_dir, exist_ok=True)
    
    print(f"Starting targeted scrape for {len(HUBS)} hubs and {len(TERMS)} terms...")
    
    for hub in HUBS:
        for term in TERMS:
            print(f"--- Scraping: {term} in {hub} ---")
            
            output_file = os.path.join(results_dir, f"{hub.replace(' ', '_')}_{term.replace(' ', '_')}.json")
            
            # Check if already scraped to avoid redundant work
            if os.path.exists(output_file):
                print(f"Skipping {hub} - {term} (already exists)")
                continue
            
            # Setup repository and use case for THIS specific scrape
            repository = JsonPlaceRepository(output_path=output_file)
            use_case = ScrapeUseCase(scraper, repository)
            
            request = ScrapeRequest(
                keyword=term,
                location=hub,
                limit=0, # Unlimited!
                output_path=output_file
            )
            
            try:
                # Run the scrape
                result = await use_case.execute(request)
                print(f"Collected {len(result.places)} places for {term} in {hub}.")
                
                # Small delay to be polite to Google
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Error scraping {term} in {hub}: {e}")

if __name__ == "__main__":
    asyncio.run(run_targeted_scrape())
