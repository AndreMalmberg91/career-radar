"""
scrapers/vc_boards.py — Scrapes job boards from Australian VC firm portfolio pages.

VC job boards are goldmines for funded startup roles that often don't
appear on mainstream job boards until days later (if at all).

VCs covered:
- Blackbird Ventures (Canva, SafetyCulture, Culture Amp)
- Airtree Ventures (largest AU portfolio support team)
- Square Peg Capital (B2B SaaS focus)
- Folklore Ventures (active B2B SaaS investor)
- Rampersand (early stage Australian SaaS)
- TEN13 (active 2026, good startup portfolio)
- Tank Stream Ventures (Sydney-focused)
"""

import requests
from bs4 import BeautifulSoup
import time


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# VC job board URLs
VC_BOARDS = [
    {
        "name": "Blackbird Ventures",
        "url": "https://jobs.blackbird.vc",
        "type": "lever"
    },
    {
        "name": "Airtree Ventures", 
        "url": "https://jobs.workable.com/jobs?companyId=b40f0b07-dd1a-4a3c-ae76-4fe983faae41",
        "type": "workable"
    },
    {
        "name": "Square Peg Capital",
        "url": "https://jobs.squarepegcap.com",
        "type": "generic"
    },
    {
        "name": "Folklore Ventures",
        "url": "https://jobs.folklore.vc",
        "type": "generic"
    },
    {
        "name": "Rampersand",
        "url": "https://rampersand.com.au/jobs",
        "type": "generic"
    },
    {
        "name": "TEN13",
        "url": "https://ten13.vc/jobs",
        "type": "generic"
    },
    {
        "name": "Tank Stream Ventures",
        "url": "https://www.tankstreamventures.com/jobs",
        "type": "generic"
    },
]

# Keywords to match CS/AM roles
CS_KEYWORDS = [
    "customer success",
    "account manager",
    "account management",
    "cs lead",
    "client success",
    "customer experience",
]


def is_relevant_role(title: str) -> bool:
    """Check if a job title is relevant to our search."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in CS_KEYWORDS)


def scrape_generic_board(vc: dict) -> list:
    """
    Generic scraper for VC job boards.
    Looks for job links and titles on the page.
    """
    jobs = []
    
    try:
        response = requests.get(vc["url"], headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"    {vc['name']} returned {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Look for job links — most VC boards use standard patterns
        job_links = soup.find_all("a", href=True)
        
        for link in job_links:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            
            if not title or len(title) < 5:
                continue
            
            # Check if this looks like a job listing
            if not is_relevant_role(title):
                continue
            
            # Build full URL
            if href.startswith("http"):
                job_url = href
            elif href.startswith("/"):
                base = vc["url"].split("/")[0] + "//" + vc["url"].split("/")[2]
                job_url = base + href
            else:
                continue
            
            # Try to find company name near the link
            parent = link.parent
            company_text = ""
            if parent:
                siblings = parent.find_all(["span", "div", "p"])
                for sib in siblings[:3]:
                    text = sib.get_text(strip=True)
                    if text and text != title and len(text) < 100:
                        company_text = text
                        break
            
            jobs.append({
                "title": title,
                "company": company_text or f"{vc['name']} Portfolio Company",
                "location": "Australia",
                "url": job_url,
                "salary_raw": None,
                "salary_min": None,
                "salary_max": None,
                "source": vc["name"],
                "is_remote": False
            })
    
    except requests.RequestException as e:
        print(f"    {vc['name']} request failed: {e}")
    
    return jobs


def scrape_vc_boards(config: dict) -> list:
    """
    Scrape all VC job boards and return relevant CS/AM roles.
    """
    all_jobs = []
    
    for vc in VC_BOARDS:
        print(f"    Checking {vc['name']} job board...")
        
        jobs = scrape_generic_board(vc)
        all_jobs.extend(jobs)
        
        # Be polite between requests
        time.sleep(2)
    
    print(f"  VC Boards: found {len(all_jobs)} relevant jobs")
    return all_jobs