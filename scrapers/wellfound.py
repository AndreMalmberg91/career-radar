"""
scrapers/wellfound.py — Scrapes job listings from Wellfound (formerly AngelList).

Wellfound is the best source for funded startup and scaleup roles.
Many APAC AI and SaaS companies post exclusively here before LinkedIn.
"""

import requests
from bs4 import BeautifulSoup
import time


WELLFOUND_BASE_URL = "https://wellfound.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}

# Wellfound role slugs that match our target titles
ROLE_SLUGS = [
    "customer-success",
    "account-management",
]

# Location filters
LOCATION_SLUGS = [
    "australia",
    "sydney",
]


def scrape_wellfound_page(url: str) -> list:
    """Scrape a single Wellfound search results page."""
    jobs = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"    Wellfound returned {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Wellfound job cards
        job_cards = soup.find_all("div", class_=lambda c: c and "job-" in c.lower())
        
        if not job_cards:
            # Try broader selector
            job_cards = soup.find_all("div", {"data-test": "StartupResult"})
        
        if not job_cards:
            # Final fallback — look for any job listing containers
            job_cards = soup.find_all("a", href=lambda h: h and "/jobs/" in str(h))
        
        for card in job_cards[:15]:
            try:
                # Try to extract job info from card
                text = card.get_text(separator=" ", strip=True)
                href = card.get("href", "")
                
                if not href or "/jobs/" not in href:
                    continue
                
                job_url = WELLFOUND_BASE_URL + href if href.startswith("/") else href
                
                # Parse text to extract title and company
                lines = [l.strip() for l in text.split("  ") if l.strip()]
                
                if len(lines) >= 2:
                    jobs.append({
                        "title": lines[0] if lines else "Unknown Role",
                        "company": lines[1] if len(lines) > 1 else "Unknown Company",
                        "location": "Australia",
                        "url": job_url,
                        "salary_raw": None,
                        "salary_min": None,
                        "salary_max": None,
                        "source": "Wellfound",
                        "is_remote": True
                    })
                    
            except Exception:
                continue
                
    except requests.RequestException as e:
        print(f"    Wellfound request failed: {e}")
    
    return jobs


def scrape_wellfound(config: dict) -> list:
    """
    Scrape Wellfound for CS and AM roles in Australia/remote.
    Returns a list of job dicts.
    """
    jobs = []
    
    for role_slug in ROLE_SLUGS:
        for location_slug in LOCATION_SLUGS:
            url = f"{WELLFOUND_BASE_URL}/role/{role_slug}?location={location_slug}"
            print(f"    Wellfound: {role_slug} in {location_slug}")
            
            page_jobs = scrape_wellfound_page(url)
            jobs.extend(page_jobs)
            
            time.sleep(2)
    
    # Also check remote APAC roles
    for role_slug in ROLE_SLUGS:
        url = f"{WELLFOUND_BASE_URL}/role/{role_slug}?remote=true"
        print(f"    Wellfound: {role_slug} remote")
        
        page_jobs = scrape_wellfound_page(url)
        # Mark as remote
        for job in page_jobs:
            job["is_remote"] = True
        jobs.extend(page_jobs)
        
        time.sleep(2)
    
    print(f"  Wellfound: found {len(jobs)} jobs")
    return jobs