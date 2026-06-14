#!/usr/bin/env bash
# verify_docker.sh — Pre-flight checks for gmaps-scraper Docker image
# Usage: bash scripts/verify_docker.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No color

IMAGE_NAME="gmaps-scraper-test"
PASSED=0
FAILED=0

run_step() {
    local step_name="$1"
    local cmd="$2"
    echo -e "\n📋 Step: ${step_name}"
    echo "   Running: ${cmd}"
    if eval "$cmd"; then
        echo -e "   ${GREEN}✅ ${step_name} — PASSED${NC}"
        ((PASSED++))
    else
        echo -e "   ${RED}❌ ${step_name} — FAILED${NC}"
        ((FAILED++))
    fi
}

echo "============================================="
echo "🐳 gmaps-scraper Docker Verification Script"
echo "============================================="

# Step 1: Build the image
run_step "Docker Build" "docker build -t ${IMAGE_NAME} ."

# Step 2: Test --help works
run_step "CLI --help" "docker run --rm ${IMAGE_NAME} python src/main.py --help"

# Step 3: Run the test suite
run_step "Test Suite" "docker run --rm ${IMAGE_NAME} python -m pytest tests/ -v"

# Step 4: Verify Playwright is installed
run_step "Playwright Check" "docker run --rm ${IMAGE_NAME} python -c \"from playwright.sync_api import sync_playwright; print('Playwright OK')\""

echo ""
echo "============================================="
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✅ Docker build verified — all ${PASSED} steps passed${NC}"
else
    echo -e "${RED}❌ ${FAILED} step(s) failed out of $((PASSED + FAILED))${NC}"
    exit 1
fi
echo "============================================="
echo ""
echo "Note: On ARM Mac (M1/M2/M3), you may need --platform linux/amd64"
