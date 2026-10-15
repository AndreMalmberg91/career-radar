"""
scrapers/linkedin.py — Scrapes LinkedIn jobs via Apify.

Uses the cheapest Apify LinkedIn scraper ($0.0005/job).
No LinkedIn account needed.
"""

import requests
import os
import time


APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "curious_coder~linkedin-jobs-scraper"


def scrape_linkedin(config: dict) -> list:
    """Search LinkedIn for CS and AM roles via Apify."""
    
    api_token = os.environ.get("APIFY_API_TOKEN")
    if not api_token:
        print("  LinkedIn: APIFY_API_TOKEN not found — skipping")
        return []

    job_titles = config.get("job_titles", [
        "Customer Success Manager",
        "Senior Customer Success Manager",
        "Account Manager"
    ])

    # Build search queries
    searches = []
    for title in job_titles[:3]:  # Limit to 3 to control cost
        searches.append({
            "keyword": title,
            "location": "Sydney, Australia",
            "dateSincePosted": "past week"
        })
    # Also search remote APAC
    searches.append({
        "keyword": "Customer Success Manager",
        "location": "Australia",
        "dateSincePosted": "past week",
        "remote": True
    })

    try:
        print(f"    LinkedIn: starting Apify scrape...")
        
        # Start the actor run
        run_response = requests.post(
            f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs",
            headers={"Authorization": f"Bearer {api_token}"},
            json={
                "searches": searches,
                "maxResults": 25
            },
            timeout=30
        )
        
        if run_response.status_code not in [200, 201]:
            print(f"    LinkedIn: Apify returned {run_response.status_code}: {run_response.text[:200]}")
            return []

        run_data = run_response.json()
        run_id = run_data.get("data", {}).get("id")
        
        if not run_id:
            print(f"    LinkedIn: no run ID returned")
            return []

        print(f"    LinkedIn: run started ({run_id}), waiting for results...")

        # Wait for run to complete (max 3 minutes)
        for attempt in range(18):
            time.sleep(10)
            
            status_response = requests.get(
                f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=15
            )
            
            if status_response.status_code != 200:
                continue
                
            status = status_response.json().get("data", {}).get("status")
            print(f"    LinkedIn: status = {status}")
            
            if status == "SUCCEEDED":
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"    LinkedIn: run {status}")
                return []

        # Fetch results
        dataset_id = status_response.json().get("data", {}).get("defaultDatasetId")
        if not dataset_id:
            print("    LinkedIn: no dataset ID")
            return []

        results_response = requests.get(
            f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
            headers={"Authorization": f"Bearer {api_token}"},
            params={"format": "json", "limit": 50},
            timeout=30
        )

        if results_response.status_code != 200:
            print(f"    LinkedIn: could not fetch results")
            return []

        raw_jobs = results_response.json()
        jobs = []
        
        for item in raw_jobs:
            title = item.get("title") or item.get("jobTitle", "")
            company = item.get("company") or item.get("companyName", "")
            location = item.get("location", "Australia")
            url = item.get("jobUrl") or item.get("url", "")
            salary = item.get("salary", None)

            if not title or not company:
                continue

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "salary_raw": salary,
                "salary_min": None,
                "salary_max": None,
                "source": "LinkedIn",
                "is_remote": "remote" in location.lower()
            })

        print(f"  LinkedIn: found {len(jobs)} jobs")
        return jobs

    except Exception as e:
        print(f"  LinkedIn scraper error: {e}")
        return []