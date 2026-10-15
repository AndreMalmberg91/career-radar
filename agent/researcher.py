"""
agent/researcher.py — Deep researches top-scoring jobs using Claude Sonnet with web search.
"""

import anthropic
import time
import os


def research_job(client: anthropic.Anthropic, job: dict) -> dict:
    """Deep research a single job using Claude Sonnet with web search."""
    
   prompt = f"""Research this job in 200 words max.

Company: {job.get('company')}
Role: {job.get('title')}
Location: {job.get('location')}

Give me:
- Company stage and funding (1 line)
- Growth: growing/stable/declining (1 line)
- Risk verdict: Worth it / Caution / Avoid (1 line + reason)
- Salary estimate AUD (1 line)
- One reason to join, one reason to avoid"""

    try:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=4000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )
        text_parts = []
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                text_parts.append(block.text)
        job["research_summary"] = "\n".join(text_parts) if text_parts else "Research unavailable"
    except Exception as e:
        print(f"    Research failed for {job.get('company')}: {e}")
        job["research_summary"] = f"Research unavailable: {str(e)}"
    
    return job


def research_top_jobs(jobs: list, config: dict) -> list:
    """Research the top N jobs by score using Claude Sonnet with web search."""
    if not jobs:
        return []
    
    max_research = config.get("max_research_roles", 5)
    top_jobs = jobs[:max_research]
    rest_jobs = jobs[max_research:]
    
    print(f"  Deep researching top {len(top_jobs)} jobs with Sonnet + web search...")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    
    for i, job in enumerate(top_jobs):
        print(f"    Researching {i+1}/{len(top_jobs)}: {job.get('company')} — {job.get('title')}")
        job = research_job(client, job)
        time.sleep(1)
    
    for job in rest_jobs:
        job["research_summary"] = None
    
    print(f"  Research complete. {len(rest_jobs)} additional jobs included with score only.")
    
    return top_jobs + rest_jobs