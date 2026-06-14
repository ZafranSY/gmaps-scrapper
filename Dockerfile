# Dockerfile for gmaps-scraper
# Single-stage build with Python + Chromium for Playwright

# Base image with Python 3.11 slim for minimal footprint
FROM python:3.11-slim

# Install system dependencies required by Playwright's Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser + system deps
RUN playwright install chromium --with-deps

# Copy the full project
COPY . .

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check to verify Playwright can start
HEALTHCHECK --interval=30s --timeout=10s --retries=1 \
    CMD python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().__enter__(); p.stop(); print('OK')" || exit 1

# Default entrypoint + show help on plain `docker run`
ENTRYPOINT ["python", "src/main.py"]
CMD ["--help"]
