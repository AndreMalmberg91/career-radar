"""
scrapers/lever.py — Scrapes job listings from Lever ATS boards.

Lever is the second most common ATS used by tech scaleups.
Public job boards are at jobs.lever.co/companyname.
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

# Known AU/APAC tech companies using Lever
LEVER_COMPANIES = [
    {"company": "Afterpay", "slug": "afterpay"},
    {"company": "Zip Co", "slug": "zip"},
    {"company": "Deputy", "slug": "deputy"},
    {"company": "Buildkite", "slug": "buildkite"},
    {"company": "Bugcrowd", "slug": "bugcrowd"},
    {"company": "Octopus Deploy", "slug": "octopusdeploy"},
    {"company": "Clipchamp", "slug": "clipchamp"},
    {"company": "Paxos", "slug": "paxos"},
    {"company": "Coassemble", "slug": "coassemble"},
    {"company": "Dovetail", "slug": "dovetailapp"},
    {"company": "Morse Micro", "slug": "morsemicro"},
    {"company": "Vervoe", "slug": "vervoe"},
    {"company": "Airtasker", "slug": "airtasker"},
    {"company": "Finder", "slug": "finder"},
    {"company": "Autopilot", "slug": "autopilot"},
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


def scrape_lever_company(company: dict) -> list:
    """Scrape a single company's Lever job board."""
    jobs = []
    url = f"https://jobs.lever.co/{company['slug']}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            return jobs

        soup = BeautifulSoup(response.text, "lxml")

        # Lever uses a standard structure with posting-title class
        postings = soup.find_all("div", class_="posting")

        if not postings:
            # Fallback to link-based approach
            job_links = soup.find_all(
                "a", href=lambda h: h and f"lever.co/{company['slug']}" in str(h)
            )
            for link in job_links:
                title = link.get_text(strip=True)
                if title and is_relevant_role(title):
                    jobs.append({
                        "title": title,
                        "company": company["company"],
                        "location": "Australia",
                        "url": link["href"],
                        "salary_raw": None,
                        "salary_min": None,
                        "salary_max": None,
                        "source": "Lever",
                        "is_remote": False
                    })
            return jobs

        for posting in postings:
            try:
                # Get title
                title_el = posting.find(
                    ["h5", "a"],
                    class_=lambda c: c and "posting-title" in str(c).lower()
                )
                if not title_el:
                    title_el = posting.find("h5")

                title = title_el.get_text(strip=True) if title_el else ""

                if not title or not is_relevant_role(title):
                    continue

                # Get location
                location_el = posting.find(
                    "span",
                    class_=lambda c: c and "location" in str(c).lower()
                )
                location = (
                    location_el.get_text(strip=True)
                    if location_el
                    else "Australia"
                )

                # Get URL
                link = posting.find("a", href=True)
                job_url = link["href"] if link else url

                jobs.append({
                    "title": title,
                    "company": company["company"],
                    "location": location,
                    "url": job_url,
                    "salary_raw": None,
                    "salary_min": None,
                    "salary_max": None,
                    "source": "Lever",
                    "is_remote": "remote" in location.lower()
                })

            except Exception:
                continue

    except requests.RequestException:
        pass

    return jobs


def scrape_lever(config: dict) -> list:
    """
    Scrape Lever boards for all known AU/APAC companies.
    Returns a list of relevant job dicts.
    """
    all_jobs = []

    for company in LEVER_COMPANIES:
        print(f"    Lever: checking {company['company']}...")
        jobs = scrape_lever_company(company)

        if jobs:
            print(f"      Found {len(jobs)} relevant roles at {company['company']}")

        all_jobs.extend(jobs)
        time.sleep(1)

    print(f"  Lever: found {len(all_jobs)} jobs")
    return all_jobs