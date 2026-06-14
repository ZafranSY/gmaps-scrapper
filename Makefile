# gmaps-scraper Makefile
# Shortcuts for Docker-based development workflows

.PHONY: build scrape test shell clean

# Build the Docker image
build:
	docker compose build

# Run the scraper with keyword and location
# Usage: make scrape KEYWORD="nasi lemak" LOCATION="Kuala Lumpur"
scrape:
	docker compose run --rm scraper python src/main.py "$(KEYWORD)" "$(LOCATION)" --output results/output.json --headless

# Run the full test suite inside the container
test:
	docker compose run --rm scraper python -m pytest tests/ -v

# Open an interactive shell inside the container
shell:
	docker compose run --rm scraper bash

# Clean up Docker resources
clean:
	docker compose down --rmi local
