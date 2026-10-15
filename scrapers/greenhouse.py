"""
scrapers/greenhouse.py — Scrapes job listings from Greenhouse ATS boards.

Greenhouse is the most common ATS used by Series B+ tech companies.
Many companies have public job boards at boards.greenhouse.io/companyname.

We search known AU/APAC tech companies that use Greenhouse.
"""

import requests
from bs4 import BeautifulSoup
import time
import re


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Known AU/APAC tech companies using Greenhouse
# Add more as you discover them
GREENHOUSE_COMPANIES = [
    {"company": "Canva", "slug": "canva"},
    {"company": "Atlassian", "slug": "atlassian"},
    {"company": "Airwallex", "slug": "airwallex"},
    {"company": "SafetyCulture", "slug": "safetyculture"},
    {"company": "Culture Amp", "slug": "cultureamp"},
    {"company": "Employment Hero", "slug": "employmenthero"},
    {"company": "Linktree", "slug": "linktree"},
    {"company": "Go1", "slug": "go1"},
    {"company": "Lendi", "slug": "lendi"},
    {"company": "Brighte", "slug": "brighte"},
    {"company": "Siteminder", "slug": "siteminder"},
    {"company": "Rokt", "slug": "rokt"},
    {"company": "Immutable", "slug": "immutable"},
    {"company": "Prospa", "slug": "prospa"},
    {"company": "Eucalyptus", "slug": "eucalyptus"},
]

CS_KEYWORDS = [
    "customer success",
    "account manager",
    "account management",
    "cs lead",
    "client success",
    "customer experience",
]


def is_relevant_role(title: str) -> bool:
    """Check if a job title matches our target roles."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in CS_KEYWORDS)


def scrape_greenhouse_company(company: dict) -> list:
    """Scrape a single company's Greenhouse job board."""
    jobs = []
    url = f"https://boards.greenhouse.io/{company['slug']}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return jobs
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Greenhouse uses a standard structure
        job_links = soup.find_all("a", href=lambda h: h and "/jobs/" in str(h))
        
        for link in job_links:
            title = link.get_text(strip=True)
            if title:
                title = re.sub(r'New(Melbourne|Sydney|Brisbane|Perth|Adelaide)', r' - \1', title)
            href = link.get("href", "")
            
            if not title or not is_relevant_role(title):
                continue
            
            job_url = (
                f"https://boards.greenhouse.io{href}" 
                if href.startswith("/") 
                else href
            )
            
            # Try to get location from nearby element
            location = "Australia"
            parent = link.find_parent(["div", "li", "tr"])
            if parent:
                location_el = parent.find(
                    ["span", "div"], 
                    class_=lambda c: c and "location" in str(c).lower()
                )
                if location_el:
                    location = location_el.get_text(strip=True)
            
            jobs.append({
                "title": title,
                "company": company["company"],
                "location": location,
                "url": job_url,
                "salary_raw": None,
                "salary_min": None,
                "salary_max": None,
                "source": "Greenhouse",
                "is_remote": False
            })
    
    except requests.RequestException:
        pass
    
    return jobs


def scrape_greenhouse(config: dict) -> list:
    """
    Scrape Greenhouse boards for all known AU/APAC companies.
    Returns a list of relevant job dicts.
    """
    all_jobs = []
    
    for company in GREENHOUSE_COMPANIES:
        print(f"    Greenhouse: checking {company['company']}...")
        jobs = scrape_greenhouse_company(company)
        
        if jobs:
            print(f"      Found {len(jobs)} relevant roles at {company['company']}")
        
        all_jobs.extend(jobs)
        time.sleep(1)
    
    print(f"  Greenhouse: found {len(all_jobs)} jobs")
    return all_jobs