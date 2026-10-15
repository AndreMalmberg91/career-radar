"""
agent/filter.py — Filters and deduplicates job listings.

Takes raw jobs from all scrapers and:
1. Removes duplicates (same job on multiple boards)
2. Filters by job title keywords
3. Filters by location (Sydney onsite/hybrid OR APAC remote)
4. Removes jobs seen in recent runs
"""

import re
from database.storage import get_seen_jobs


# Title keywords that must appear in the job title
TITLE_KEYWORDS = [
    "customer success",
    "account manager",
    "cs lead",
    "cs manager",
    "client success",
    "founding csm",
]

# Keywords that disqualify a role (to reduce noise)
NEGATIVE_KEYWORDS = [
    "director",
    "vp ",
    "vice president",
    "chief",
    "intern",
    "graduate",
    "junior",
]

# Sydney location signals
SYDNEY_KEYWORDS = ["sydney", "nsw", "new south wales"]

# Remote/APAC signals
REMOTE_KEYWORDS = ["remote", "apac", "australia", "anywhere"]


def matches_title(job: dict, config: dict) -> bool:
    """Check if job title matches our target roles."""
    title = job.get("title", "").lower()
    
    # Check configured titles first
    configured_titles = [t.lower() for t in config.get("job_titles", [])]
    for configured in configured_titles:
        if configured in title:
            return True
    
    # Fall back to keyword matching
    for keyword in TITLE_KEYWORDS:
        if keyword in title:
            # Make sure it's not a negative match
            for negative in NEGATIVE_KEYWORDS:
                if negative in title:
                    return False
            return True
    
    return False


def matches_location(job: dict) -> tuple[bool, bool]:
    """
    Check if job matches location requirements.
    Only accepts roles explicitly in Australia/Sydney or explicitly remote.
    Returns (matches, is_remote) tuple.
    """
    location = job.get("location", "").lower()
    description = job.get("description", "").lower()
    combined = f"{location} {description}"

    # Must explicitly mention Australia or remote to be included
    australia_signals = [
        "sydney", "nsw", "new south wales",
        "melbourne", "victoria", "brisbane", "queensland",
        "perth", "western australia", "adelaide", "south australia",
        "australia", "au", "canberra", "act"
    ]

    remote_signals = [
        "remote - australia", "remote australia",
        "apac remote", "remote apac",
        "anywhere in australia", "australia (remote)",
        "remote (australia)"
    ]

    is_sydney = any(kw in location for kw in australia_signals)
    is_remote = any(kw in combined for kw in remote_signals)

    # If location is empty or just says "remote" with no region — skip it
    if not location or location.strip() in ["remote", "anywhere", ""]:
        return False, False

    matches = is_sydney or is_remote
    return matches, is_remote

def deduplicate(jobs: list) -> list:
    """Remove duplicate jobs based on company + title combination."""
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        # Create a normalised key for deduplication
        company = re.sub(r'[^a-z0-9]', '', job.get("company", "").lower())
        title = re.sub(r'[^a-z0-9]', '', job.get("title", "").lower())
        key = f"{company}_{title}"
        
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    return unique_jobs


def remove_recently_seen(jobs: list, db_path: str) -> list:
    """Remove jobs we've already shown in recent runs."""
    seen_jobs = get_seen_jobs(db_path, days=3)
    
    new_jobs = []
    for job in jobs:
        key = (job.get("company", "").lower(), job.get("title", "").lower())
        if key not in seen_jobs:
            new_jobs.append(job)
    
    return new_jobs


def filter_jobs(jobs: list, config: dict, db_path: str) -> list:
    """
    Main filter function. Takes all scraped jobs and returns
    only the relevant, unique, new ones.
    """
    print(f"  Filtering {len(jobs)} raw jobs...")
    
    filtered = []
    for job in jobs:
        # Must match title
        if not matches_title(job, config):
            continue
        
        # Must match location
        matches, is_remote = matches_location(job)
        if not matches:
            continue
        
        job["is_remote"] = is_remote
        filtered.append(job)
    
    print(f"  {len(filtered)} jobs after title/location filter")
    
    # Remove duplicates across sources
    filtered = deduplicate(filtered)
    print(f"  {len(filtered)} jobs after deduplication")
    
    # Remove jobs seen in recent runs
    filtered = remove_recently_seen(filtered, db_path)
    print(f"  {len(filtered)} new jobs (not seen recently)")
    
    return filtered