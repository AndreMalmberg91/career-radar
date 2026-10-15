"""
agent/researcher.py — Deep researches top-scoring jobs using Claude Sonnet with web search.
"""

import anthropic
import time
import os


def research_job(client: anthropic.Anthropic, job: dict) -> dict:
    """Deep research a single job using Claude Sonnet with web search tool."""
    
    prompt = f"""Research this company and job opportunity thoroughly using web search.

Company: {job.get('company')}
Role: {job.get('title')}
Location: {job.get('location')}
Salary listed: {job.get('salary_raw', 'Not listed')}

Search for current information and provide:

1. COMPANY OVERVIEW - What they do, stage, funding, revenue, headcount
2. GROWTH TRAJECTORY - Growing, stable or declining? Recent news and signals
3. CAREER RISK VERDICT - Worth the risk / Proceed with caution / Avoid + why
4. EXPECTED COMPENSATION (AUD) - Based on current market data for this role in Australia
5. WHY JOIN / WHY AVOID - 2 concrete reasons each

Use web search to find real current data. Be specific with numbers and dates."""

    try:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=2000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract text from response blocks
        text_parts = []
        for block in response.content:
            if hasattr(block, 'text'):
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