"""
scrapers/seek.py — Scrapes job listings from Seek.com.au

Seek is Australia's largest job board and is scraper-friendly.
We search for each job title and extract the key fields.
"""

import requests
from bs4 import BeautifulSoup
import time
import re


SEEK_BASE_URL = "https://www.seek.com.au"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}


def build_seek_url(job_title: str, location: str = "Sydney NSW") -> str:
    """Build a Seek search URL for a given job title and location."""
    # Format title for URL
    title_slug = job_title.lower().replace(" ", "-")
    location_slug = location.lower().replace(" ", "-")
    return f"{SEEK_BASE_URL}/{title_slug}-jobs/in-{location_slug}"


def parse_salary(salary_text: str) -> tuple:
    """Extract min/max salary from salary text."""
    if not salary_text:
        return None, None
    
    # Find all numbers in the salary text
    numbers = re.findall(r'\d+(?:,\d+)?(?:\.\d+)?[kK]?', salary_text)
    
    amounts = []
    for num in numbers:
        num = num.replace(',', '')
        if num.lower().endswith('k'):
            amounts.append(int(float(num[:-1]) * 1000))
        else:
            try:
                amounts.append(int(float(num)))
            except:
                pass
    
    if len(amounts) >= 2:
        return min(amounts), max(amounts)
    elif len(amounts) == 1:
        return amounts[0], amounts[0]
    return None, None


def scrape_seek(config: dict) -> list:
    """
    Scrape Seek for all configured job titles.
    Returns a list of job dicts.
    """
    jobs = []
    job_titles = config.get("job_titles", [])
    locations = config.get("locations", {})
    onsite_locations = locations.get("onsite", ["Sydney"])
    
    for title in job_titles:
        for location in onsite_locations:
            url = build_seek_url(title, location)
            
            try:
                print(f"    Seeking: {title} in {location}")
                response = requests.get(url, headers=HEADERS, timeout=10)
                
                if response.status_code != 200:
                    print(f"    Seek returned {response.status_code} for {title}")
                    continue
                
                soup = BeautifulSoup(response.text, "lxml")
                
                # Find job cards — Seek uses data-automation attributes
                job_cards = soup.find_all("article", {"data-automation": "normalJob"})
                
                if not job_cards:
                    # Try alternative selector
                    job_cards = soup.find_all("article")
                
                for card in job_cards[:10]:  # Max 10 per search
                    try:
                        # Extract job details
                        title_el = card.find(
                            ["a", "h3", "span"], 
                            {"data-automation": "jobTitle"}
                        )
                        company_el = card.find(
                            ["a", "span"], 
                            {"data-automation": "jobCompany"}
                        )
                        location_el = card.find(
                            ["a", "span"], 
                            {"data-automation": "jobLocation"}
                        )
                        salary_el = card.find(
                            ["span"], 
                            {"data-automation": "jobSalary"}
                        )
                        
                        job_title = title_el.get_text(strip=True) if title_el else None
                        company = company_el.get_text(strip=True) if company_el else None
                        job_location = location_el.get_text(strip=True) if location_el else location
                        salary_raw = salary_el.get_text(strip=True) if salary_el else None
                        
                        # Get job URL
                        link = card.find("a", {"data-automation": "jobTitle"})
                        job_url = SEEK_BASE_URL + link["href"] if link and link.get("href") else url
                        
                        if not job_title or not company:
                            continue
                        
                        salary_min, salary_max = parse_salary(salary_raw)
                        
                        jobs.append({
                            "title": job_title,
                            "company": company,
                            "location": job_location,
                            "url": job_url,
                            "salary_raw": salary_raw,
                            "salary_min": salary_min,
                            "salary_max": salary_max,
                            "source": "Seek",
                            "is_remote": False
                        })
                        
                    except Exception as e:
                        continue
                
                # Be polite — don't hammer Seek
                time.sleep(2)
                
            except requests.RequestException as e:
                print(f"    Seek request failed: {e}")
                continue
    
    print(f"  Seek: found {len(jobs)} jobs")
    return jobs