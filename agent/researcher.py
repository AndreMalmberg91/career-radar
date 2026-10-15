"""
agent/researcher.py — Deep researches top-scoring jobs using Claude Sonnet.

Only runs on the top N jobs (configured in config.yaml) to keep costs low.
Sonnet is more capable than Haiku and gives thorough company analysis.
"""

import anthropic
import time


def research_job(client: anthropic.Anthropic, job: dict) -> dict:
    """
    Deep research a single job using Claude Sonnet with web search.
    Returns the job with detailed research summary added.
    """
    
    prompt = f"""You are a career intelligence analyst helping a senior Customer Success Manager 
evaluate whether to apply for this role. Research this company and role thoroughly.

Company: {job.get('company')}
Role: {job.get('title')}
Location: {job.get('location')}
Salary listed: {job.get('salary_raw', 'Not listed')}

Provide a structured analysis covering:

1. COMPANY OVERVIEW
   - What they do and who their customers are
   - Company stage (seed/Series A/B/C/D/public)
   - Total funding raised and key investors
   - Revenue or ARR if known
   - Headcount and growth trajectory

2. GROWTH TRAJECTORY
   - Is this company growing, stable or declining?
   - Key growth signals (funding, hiring, product launches, press)
   - Red flags if any (layoffs, pivots, leadership changes)

3. CAREER RISK VERDICT
   - Worth the risk / Proceed with caution / Avoid
   - One paragraph explaining why

4. EXPECTED COMPENSATION (AUD)
   - Estimated base salary range
   - Equity/bonus expectations
   - How you estimated this

5. WHY JOIN / WHY AVOID
   - 2 strong reasons to join
   - 2 honest reasons to think twice

Keep each section concise. Base your analysis on what you know about this company.
If you don't have information, say so rather than guessing."""

    try:
        response = client.messages.create(
            model="claude-haiku-5-5-20251022",
            max_tokens=1000,
            timeout=60,
            messages=[{"role": "user", "content": prompt}]
        )
        
        job["research_summary"] = response.content[0].text
        
    except Exception as e:
        print(f"    Research failed for {job.get('company')}: {e}")
        job["research_summary"] = f"Research unavailable: {str(e)}"
    
    return job


def research_top_jobs(jobs: list, config: dict) -> list:
    """
    Research the top N jobs by score using Claude Sonnet.
    Lower-scoring jobs get the Haiku score reason only (no deep research).
    """
    if not jobs:
        return []
    
    max_research = config.get("max_research_roles", 5)
    
    # Split into top jobs (get deep research) and rest (score reason only)
    top_jobs = jobs[:max_research]
    rest_jobs = jobs[max_research:]
    
    print(f"  Deep researching top {len(top_jobs)} jobs with Sonnet...")
    
    client = anthropic.Anthropic()
    
    for i, job in enumerate(top_jobs):
        print(f"    Researching {i+1}/{len(top_jobs)}: {job.get('company')} — {job.get('title')}")
        job = research_job(client, job)
        
        # Delay between API calls
        time.sleep(1)
    
    # Mark remaining jobs as not deeply researched
    for job in rest_jobs:
        job["research_summary"] = None
    
    print(f"  Research complete. {len(rest_jobs)} additional jobs included with score only.")
    
    return top_jobs + rest_jobs