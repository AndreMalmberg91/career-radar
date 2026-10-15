import anthropic
import time
import os


def research_job(client, job):
    prompt = f"""Research this job briefly. Use web search. Max 150 words total.

Company: {job.get('company')}
Role: {job.get('title')}
Location: {job.get('location')}

Answer in this exact format:
STAGE: [funding stage and amount]
GROWTH: [growing/stable/declining + one reason]
VERDICT: [Worth it/Caution/Avoid] - [one sentence why]
SALARY: [estimated AUD base range]
JOIN: [one reason]
AVOID: [one reason]"""

    try:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=300,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )
        text_parts = [block.text for block in response.content if hasattr(block, 'text') and block.text]
        job["research_summary"] = "\n".join(text_parts) if text_parts else "Research unavailable"
    except Exception as e:
        print(f"    Research failed for {job.get('company')}: {e}")
        job["research_summary"] = None
    return job


def research_top_jobs(jobs, config):
    if not jobs:
        return []
    max_research = config.get("max_research_roles", 5)
    top_jobs = jobs[:max_research]
    rest_jobs = jobs[max_research:]
    print(f"  Researching top {len(top_jobs)} jobs...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    for i, job in enumerate(top_jobs):
        print(f"    {i+1}/{len(top_jobs)}: {job.get('company')} - {job.get('title')}")
        job = research_job(client, job)
        time.sleep(1)
    for job in rest_jobs:
        job["research_summary"] = None
    print(f"  Research complete.")
    return top_jobs + rest_jobs