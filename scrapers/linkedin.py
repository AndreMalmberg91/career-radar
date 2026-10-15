"""
scrapers/linkedin.py — Scrapes LinkedIn jobs via Apify.
"""

import requests
import os
import time


APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "curious_coder~linkedin-jobs-scraper"


def scrape_linkedin(config: dict) -> list:
    api_token = os.environ.get("APIFY_API_TOKEN")
    if not api_token:
        print("  LinkedIn: APIFY_API_TOKEN not found — skipping")
        return []

    all_jobs = []
    
    # Search queries using correct input format
    queries = [
        {"keywords": "Customer Success Manager", "location": "Sydney, Australia"},
        {"keywords": "Senior Customer Success Manager", "location": "Sydney, Australia"},
        {"keywords": "Enterprise Customer Success Manager", "location": "Australia"},
        {"keywords": "Account Manager SaaS", "location": "Sydney, Australia"},
    ]

    for query in queries:
        try:
            print(f"    LinkedIn: searching '{query['keywords']}' in {query['location']}")
            
            run_response = requests.post(
                f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs",
                headers={"Authorization": f"Bearer {api_token}"},
                json={
                    "keywords": query["keywords"],
                    "location": query["location"],
                    "datePosted": "past week",
                    "limit": 15
                },
                timeout=30
            )
            
            if run_response.status_code not in [200, 201]:
                print(f"    LinkedIn: error {run_response.status_code}")
                continue

            run_id = run_response.json().get("data", {}).get("id")
            if not run_id:
                continue

            # Wait for completion
            for _ in range(18):
                time.sleep(10)
                status_resp = requests.get(
                    f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                    headers={"Authorization": f"Bearer {api_token}"},
                    timeout=15
                )
                status = status_resp.json().get("data", {}).get("status")
                if status == "SUCCEEDED":
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    break

            dataset_id = status_resp.json().get("data", {}).get("defaultDatasetId")
            if not dataset_id:
                continue

            results = requests.get(
                f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
                headers={"Authorization": f"Bearer {api_token}"},
                params={"format": "json", "limit": 20},
                timeout=30
            ).json()

            for item in results:
                title = item.get("title", "")
                company = item.get("companyName", "")
                if not title or not company:
                    continue

                salary = None
                salary_info = item.get("salaryInfo")
                if salary_info and isinstance(salary_info, list) and len(salary_info) >= 2:
                    salary = f"{salary_info[0]} - {salary_info[1]}"

                all_jobs.append({
                    "title": title,
                    "company": company,
                    "location": item.get("location", query["location"]),
                    "url": item.get("link", ""),
                    "salary_raw": salary,
                    "salary_min": None,
                    "salary_max": None,
                    "source": "LinkedIn",
                    "is_remote": item.get("workRemoteAllowed", False)
                })

        except Exception as e:
            print(f"    LinkedIn error: {e}")
            continue

    print(f"  LinkedIn: found {len(all_jobs)} jobs")
    return all_jobs