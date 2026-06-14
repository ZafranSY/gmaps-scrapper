
import asyncio
from src.infrastructure.scraping.playwright_scraper import PlaywrightGoogleMapsScraper

def test_classification():
    scraper = PlaywrightGoogleMapsScraper()
    
    test_urls = [
        "https://linktr.ee/user",
        "https://wa.me/123456789",
        "https://www.facebook.com/group",
        "https://www.instagram.com/profile",
        "https://official-website.com"
    ]
    
    for url in test_urls:
        classification = scraper._classify_website(url)
        print(f"URL: {url} -> Classification: {classification}")

if __name__ == "__main__":
    test_classification()
