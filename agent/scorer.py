"""
agent/scorer.py — Scores each job 1-10 using Claude Haiku.
"""

import anthropic
import json
import time
import os


def score_job(client: anthropic.Anthropic, job: dict) -> dict:
    """Score a single job 1-10 using Claude Haiku."""
    
    prompt = f"""You are a job market analyst helping a senior Customer Success Manager 
with 7+ years experience evaluate job opportunities.

Score this job from 1-10 based on:
- Company stage and growth (prefer Series A-D startups and scaleups)
- Role seniority and scope
- Whether it's an AI-native or tech-forward company
- Compensation potential (prefer AUD $130K-180K base)
- Career trajectory value

Job details:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Source: {job.get('source', 'Unknown')}
Remote: {job.get('is_remote', False)}
Salary info: {job.get('salary_raw', 'Not listed')}

Respond with JSON only:
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
text_content = next((block.text for block in response.content if hasattr(block, 'text')), None)
result = json.loads(text_content)
job["score"] = result.get("score", 0)
        job["score_reason"] = result.get("reason", "")
        job["company_stage"] = result.get("company_stage", "unknown")
        job["red_flags"] = result.get("red_flags", "none")
    except Exception as e:
        print(f"    Scoring failed for {job.get('company')}: {e}")
        job["score"] = 5
        job["score_reason"] = "Could not score automatically"
        job["company_stage"] = "unknown"
        job["red_flags"] = "none"
    
    return job


def score_jobs(jobs: list, config: dict) -> list:
    """Score all jobs using Haiku and return sorted by score."""
    if not jobs:
        return []
    
    print(f"  Scoring {len(jobs)} jobs with Haiku...")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    
    min_score = config.get("min_score", 5)
    scored_jobs = []
    
    for i, job in enumerate(jobs):
        print(f"    Scoring {i+1}/{len(jobs)}: {job.get('company')} — {job.get('title')}")
        job = score_job(client, job)
        if job["score"] >= min_score:
            scored_jobs.append(job)
        time.sleep(0.5)
    
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    print(f"  {len(scored_jobs)} jobs scored {min_score}+ (out of {len(jobs)})")
    return scored_jobs