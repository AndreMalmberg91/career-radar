"""
scrapers/indeed.py — Scrapes job listings from Indeed Australia.

Indeed has broad coverage and catches many roles that don't appear
on specialist boards. We use their public search pages.
"""

import requests
from bs4 import BeautifulSoup
import time
import urllib.parse


INDEED_BASE_URL = "https://au.indeed.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Combine titles into fewer searches to stay within free tier limits
SEARCH_QUERIES = [
    "Customer Success Manager OR Senior Customer Success Manager",
    "Enterprise Customer Success Manager OR Customer Success Lead",
    "Account Manager SaaS OR Founding Customer Success",
]

LOCATIONS = [
    "Sydney NSW",
    "Remote Australia",
]


def build_indeed_url(query: str, location: str) -> str:
    """Build an Indeed search URL."""
    params = urllib.parse.urlencode({
        "q": query,
        "l": location,
        "fromage": "7",  # Posted in last 7 days
        "sort": "date",
    })
    return f"{INDEED_BASE_URL}/jobs?{params}"


def scrape_indeed_page(url: str) -> list:
    """Scrape a single Indeed results page."""
    jobs = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            print(f"    Indeed returned {response.status_code}")
            return jobs

        soup = BeautifulSoup(response.text, "lxml")

        # Indeed job cards
        job_cards = soup.find_all("div", class_=lambda c: c and "job_seen_beacon" in str(c))

        if not job_cards:
            # Try alternative selectors
            job_cards = soup.find_all("td", class_=lambda c: c and "resultContent" in str(c))

        if not job_cards:
            job_cards = soup.find_all("div", {"data-testid": "slider_container"})

        for card in job_cards[:10]:
            try:
                # Title
                title_el = card.find(
                    ["h2", "span"],
                    class_=lambda c: c and "jobTitle" in str(c)
                )
                if not title_el:
                    title_el = card.find("h2")

                title = title_el.get_text(strip=True) if title_el else None

                if not title:
                    continue

                # Company
                company_el = card.find(
                    ["span", "a"],
                    {"data-testid": "company-name"}
                )
                if not company_el:
                    company_el = card.find(
                        "span",
                        class_=lambda c: c and "companyName" in str(c)
                    )

                company = company_el.get_text(strip=True) if company_el else "Unknown"

                # Location
                location_el = card.find(
                    ["div", "span"],
                    {"data-testid": "text-location"}
                )
                location = location_el.get_text(strip=True) if location_el else "Australia"

                # Salary
                salary_el = card.find(
                    ["div", "span"],
                    class_=lambda c: c and "salary" in str(c).lower()
                )
                salary_raw = salary_el.get_text(strip=True) if salary_el else None

                # URL
                link = card.find("a", href=lambda h: h and "/rc/clk" in str(h))
                if not link:
                    link = card.find("a", href=True)

                job_url = (
                    INDEED_BASE_URL + link["href"]
                    if link and link["href"].startswith("/")
                    else (link["href"] if link else url)
                )

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": job_url,
                    "salary_raw": salary_raw,
                    "salary_min": None,
                    "salary_max": None,
                    "source": "Indeed",
                    "is_remote": "remote" in location.lower()
                })

            except Exception:
                continue

    except requests.RequestException as e:
        print(f"    Indeed request failed: {e}")

    return jobs


def scrape_indeed(config: dict) -> list:
    """
    Scrape Indeed Australia for all target job titles.
    Combines titles into fewer searches to stay within limits.
    Returns a list of job dicts.
    """
    all_jobs = []

    for query in SEARCH_QUERIES:
        for location in LOCATIONS:
            url = build_indeed_url(query, location)
            print(f"    Indeed: '{query[:40]}...' in {location}")

            jobs = scrape_indeed_page(url)
            all_jobs.extend(jobs)

            # Be respectful — Indeed blocks aggressive scrapers
            time.sleep(3)

    print(f"  Indeed: found {len(all_jobs)} jobs")
    return all_jobs