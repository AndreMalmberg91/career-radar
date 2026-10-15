"""
scrapers/adzuna.py — Scrapes job listings from Adzuna API.

Adzuna aggregates jobs from Seek, Indeed and hundreds of other Australian
job boards. Uses official API — no blocking, reliable from GitHub Actions.
"""

import requests
import os
import time

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/au/search"

CS_KEYWORDS = [
    "Customer Success Manager",
    "Senior Customer Success Manager",
    "Enterprise Customer Success Manager",
    "Account Manager",
    "Customer Success Lead",
    "Founding Customer Success",
]


def scrape_adzuna(config: dict) -> list:
    """
    Search Adzuna for CS and AM roles in Australia.
    Returns a list of job dicts.
    """
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    
    if not app_id or not app_key:
        print("  Adzuna: API credentials not found — skipping")
        return []
    
    all_jobs = []
    
    # Search queries — combine titles to save API calls
    search_queries = [
        "Customer Success Manager",
        "Enterprise Customer Success Manager",
        "Account Manager SaaS",
    ]
    
    locations = ["Sydney", "Australia"]
    
    for query in search_queries:
        for location in locations:
            try:
                print(f"    Adzuna: '{query}' in {location}")
                
                params = {
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": 10,
                    "what": query,
                    "where": location,
                    "content-type": "application/json",
                    "sort_by": "date",
                }
                
                response = requests.get(
                    f"{ADZUNA_BASE_URL}/1",
                    params=params,
                    timeout=15
                )
                
                if response.status_code != 200:
                    print(f"    Adzuna returned {response.status_code}")
                    continue
                
                data = response.json()
                results = data.get("results", [])
                
                for job in results:
                    salary_min = job.get("salary_min")
                    salary_max = job.get("salary_max")
                    salary_raw = None
                    if salary_min and salary_max:
                        salary_raw = f"${int(salary_min):,} - ${int(salary_max):,}"
                    elif salary_min:
                        salary_raw = f"${int(salary_min):,}+"
                    
                    all_jobs.append({
                        "title": job.get("title", "Unknown"),
                        "company": job.get("company", {}).get("display_name", "Unknown"),
                        "location": job.get("location", {}).get("display_name", location),
                        "url": job.get("redirect_url", ""),
                        "salary_raw": salary_raw,
                        "salary_min": int(salary_min) if salary_min else None,
                        "salary_max": int(salary_max) if salary_max else None,
                        "source": "Adzuna",
                        "is_remote": "remote" in job.get("title", "").lower() or 
                                    "remote" in job.get("location", {}).get("display_name", "").lower()
                    })
                
                print(f"    Adzuna: found {len(results)} jobs for '{query}' in {location}")
                time.sleep(1)
                
            except Exception as e:
                print(f"    Adzuna error: {e}")
                continue
    
    print(f"  Adzuna: {len(all_jobs)} total jobs found")
    return all_jobs