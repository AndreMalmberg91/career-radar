"""
agent/scorer.py — Scores each job 1-10 using Claude Haiku.
"""

import anthropic
import json
import time
import os


def score_job(client: anthropic.Anthropic, job: dict) -> dict:
    """Score a single job 1-10 using Claude Haiku."""
    
    prompt = f"""You are a job market analyst. Score this job from 1-10.

Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Remote: {job.get('is_remote', False)}
Salary: {job.get('salary_raw', 'Not listed')}

Score based on: company stage/growth, role seniority, AI/tech focus, AUD $130K-180K comp potential.

Respond with JSON only, no other text:
{{"score": 7, "reason": "one sentence", "company_stage": "startup", "red_flags": "none"}}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text
        result = json.loads(text)
        job["score"] = result.get("score", 5)
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