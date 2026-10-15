"""
agent/researcher.py — Deep researches top-scoring jobs using Claude Sonnet.
"""

import anthropic
import httpx
import time


def research_job(client: anthropic.Anthropic, job: dict) -> dict:
    """Deep research a single job using Claude Sonnet."""
    
    prompt = f"""You are a career intelligence analyst helping a senior Customer Success Manager 
evaluate whether to apply for this role. Research this company and role thoroughly.

Company: {job.get('company')}
Role: {job.get('title')}
Location: {job.get('location')}
Salary listed: {job.get('salary_raw', 'Not listed')}

Provide a structured analysis covering:

1. COMPANY OVERVIEW - What they do, stage, funding, revenue, headcount
2. GROWTH TRAJECTORY - Growing, stable or declining? Key signals and red flags
3. CAREER RISK VERDICT - Worth the risk / Proceed with caution / Avoid + why
4. EXPECTED COMPENSATION (AUD) - Estimated base salary range
5. WHY JOIN / WHY AVOID - 2 reasons each

Keep each section concise. If you don't have information, say so."""

    try:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        job["research_summary"] = response.content[0].text
    except Exception as e:
        print(f"    Research failed for {job.get('company')}: {e}")
        job["research_summary"] = f"Research unavailable: {str(e)}"
    
    return job


def research_top_jobs(jobs: list, config: dict) -> list:
    """Research the top N jobs by score using Claude Sonnet."""
    if not jobs:
        return []
    
    max_research = config.get("max_research_roles", 5)
    top_jobs = jobs[:max_research]
    rest_jobs = jobs[max_research:]
    
    print(f"  Deep researching top {len(top_jobs)} jobs with Sonnet...")
    
    client = anthropic.Anthropic(
        max_retries=3,
        http_client=httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0)
        ),
    )
    
    for i, job in enumerate(top_jobs):
        print(f"    Researching {i+1}/{len(top_jobs)}: {job.get('company')} — {job.get('title')}")
        job = research_job(client, job)
        time.sleep(1)
    
    for job in rest_jobs:
        job["research_summary"] = None
    
    print(f"  Research complete. {len(rest_jobs)} additional jobs included with score only.")
    
    return top_jobs + rest_jobs