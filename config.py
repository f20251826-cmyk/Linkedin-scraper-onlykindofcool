"""
config.py — Central configuration for the LinkedIn Search Scraper.
Edit the constants below to customise behaviour.
"""

import os

# ──────────────────────────────────────────────
# Target roles to search for at each company
# ──────────────────────────────────────────────
TARGET_ROLES: list[str] = [
    "Founder",
    "Strategic Partnerships",
    "Sponsorships",
    "Alliance",
    "Brand Engagement",
    "PR",
    "CSR",
    "Founder's Office",
    "Corporate Communications",
    "Finance",
]

# ──────────────────────────────────────────────
# Scraping limits
# ──────────────────────────────────────────────
MAX_RESULTS_PER_SEARCH: int = 10       # How many profiles to scrape per search

# ──────────────────────────────────────────────
# Timing / anti-detection
# ──────────────────────────────────────────────
INTER_COMPANY_DELAY: tuple[int, int] = (3, 5)       # Seconds between different company searches
INTER_ROLE_DELAY: tuple[int, int] = (1, 3)           # Seconds between role searches within the same company
SCROLL_RANGE: tuple[int, int] = (200, 500)           # Random scroll distance in pixels
SCROLL_PAUSE: tuple[float, float] = (0.3, 0.8)      # Pause between scroll steps (seconds)
SCROLL_STEPS: tuple[int, int] = (2, 4)              # Number of scroll actions per page

# ──────────────────────────────────────────────
# File paths
# ──────────────────────────────────────────────
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV: str = os.path.join(BASE_DIR, "companies.csv")
OUTPUT_CSV: str = os.path.join(BASE_DIR, "results.csv")
BROWSER_DATA_DIR: str = os.path.join(BASE_DIR, "browser_data")
