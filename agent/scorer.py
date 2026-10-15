"""
agent/scorer.py — Scores each job 1-10 using Claude Haiku.

Haiku is the cheapest Claude model and is more than capable of
scoring jobs based on a structured prompt. We only use the more
expensive Sonnet model for deep research on top-scoring roles.
"""

import anthropic
import json
import time


def score_job(client: anthropic.Anthropic, job: dict) -> dict:
    """
    Score a single job 1-10 using Claude Haiku.
    Returns the job with score and scoring reason added.
    """
    
    prompt = f"""You are a job market analyst helping a senior Customer Success Manager 
with 7+ years experience evaluate job opportunities.

Score this job from 1-10 based on these criteria:
- Company stage and growth (prefer Series A-D startups and scaleups)
- Role seniority and scope (prefer senior individual contributor or lead roles)
- Whether it's an AI-native or tech-forward company
- Compensation potential (prefer roles likely to pay AUD $130K-180K base)
- Career trajectory value (will this role accelerate their career?)

Job details:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Source: {job.get('source', 'Unknown')}
Remote: {job.get('is_remote', False)}
Salary info: {job.get('salary_raw', 'Not listed')}

Respond with JSON only, no other text:
{{
  "score": <integer 1-10>,
  "reason": "<one sentence explaining the score>",
  "company_stage": "<startup/scaleup/enterprise/unknown>",
  "red_flags": "<any concerns, or none>"
}}"""

    try:
        response = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse the JSON response
        result = json.loads(response.content[0].text)
        
        job["score"] = result.get("score", 0)
        job["score_reason"] = result.get("reason", "")
        job["company_stage"] = result.get("company_stage", "unknown")
        job["red_flags"] = result.get("red_flags", "none")
        
    except (json.JSONDecodeError, Exception) as e:
        # If scoring fails, give a neutral score
        print(f"    Scoring failed for {job.get('company')}: {e}")
        job["score"] = 5
        job["score_reason"] = "Could not score automatically"
        job["company_stage"] = "unknown"
        job["red_flags"] = "none"
    
    return job


def score_jobs(jobs: list, config: dict) -> list:
    """
    Score all jobs using Haiku and return sorted by score.
    Only returns jobs meeting the minimum score threshold.
    """
    if not jobs:
        return []
    
    print(f"  Scoring {len(jobs)} jobs with Haiku...")
    
    # Initialise Anthropic client
    client = anthropic.Anthropic()
    
    min_score = config.get("min_score", 5)
    scored_jobs = []
    
    for i, job in enumerate(jobs):
        print(f"    Scoring {i+1}/{len(jobs)}: {job.get('company')} — {job.get('title')}")
        job = score_job(client, job)
        
        if job["score"] >= min_score:
            scored_jobs.append(job)
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Sort by score highest first
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"  {len(scored_jobs)} jobs scored {min_score}+ (out of {len(jobs)})")
    return scored_jobs